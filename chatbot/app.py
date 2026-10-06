#!/usr/bin/env python3
"""CLI: red-team agent against the local pancake chatbot."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow `python app.py` from chatbot/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.table import Table

from owasp_checklist import checklist_markdown

console = Console()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Red-team kit dla własnego chatbota naleśnikowego "
            "(HF prompts + Gemini attacker/judge + logi tur)."
        )
    )
    p.add_argument(
        "--mode",
        choices=["all", "single", "multi", "adaptive", "checklist"],
        default="all",
        help="Rodzaj ataków (domyślnie: all)",
    )
    p.add_argument("--repeats", type=int, default=None, help="Powtórzeń per prompt (10–20)")
    p.add_argument("--max-prompts", type=int, default=None, help="Ile promptów z HF")
    p.add_argument("--multi-rounds", type=int, default=None)
    p.add_argument("--adaptive-rounds", type=int, default=None)
    p.add_argument("--campaigns", type=int, default=3, help="Ile kampanii multi/adaptive")
    p.add_argument(
        "--no-llm-judge",
        action="store_true",
        help="Tylko heurystyki słów kluczowych (bez Gemini judge)",
    )
    p.add_argument(
        "--no-rewrite",
        action="store_true",
        help="Nie przepisuj promptów HF pod scope naleśników",
    )
    p.add_argument("--run-name", type=str, default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.mode == "checklist":
        console.print(checklist_markdown())
        out = Path(__file__).resolve().parent / "logs"
        out.mkdir(parents=True, exist_ok=True)
        path = out / "owasp_llm01_checklist.md"
        path.write_text(checklist_markdown(), encoding="utf-8")
        console.print(f"[green]Zapisano {path}[/green]")
        return 0

    # Lazy imports — wymagają .env z GEMINI-API
    try:
        from attacks import run_adaptive, run_multi_turn, run_single_turn
        from config import settings
        from hf_prompts import iter_unique, load_attack_prompts
        from logging_utils import RunLogger
        from target_client import TargetClient
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        return 1

    repeats = args.repeats or settings.repeats
    max_prompts = args.max_prompts or settings.max_prompts
    multi_rounds = args.multi_rounds or settings.multi_turn_rounds
    adaptive_rounds = args.adaptive_rounds or settings.adaptive_rounds
    use_llm = not args.no_llm_judge

    console.print("[bold]Chatbot Red-Team Kit[/bold]")
    console.print(f"Target: {settings.target_url}")
    console.print(f"HF dataset: {settings.hf_dataset}")
    console.print(f"Attacker: {settings.attacker_model} | Judge: {settings.judge_model}")
    console.print(
        f"Repeats/prompt: {repeats} | Max prompts: {max_prompts} | "
        f"Rate limit: {settings.max_qpm}/min"
    )
    console.print(
        "Sesje: single=nowy chat/próba | multi+adaptive=jeden chat na kampanię"
    )

    logger = RunLogger(args.run_name)
    summaries: list[dict] = []

    with TargetClient() as target:
        if not target.healthcheck():
            console.print(
                f"[red]Target niedostępny: {settings.target_url}. "
                "Uruchom chatbota na :8080.[/red]"
            )
            return 2

        prompts = []
        if args.mode in ("all", "single"):
            prompts = iter_unique(load_attack_prompts(max_prompts))
            console.print(f"Załadowano {len(prompts)} unikalnych promptów ataku")

        if args.mode in ("all", "single"):
            console.rule("Single-turn")
            summaries.append(
                run_single_turn(
                    prompts,
                    target,
                    logger,
                    repeats=repeats,
                    use_llm_judge=use_llm,
                    rewrite=not args.no_rewrite,
                )
            )

        if args.mode in ("all", "multi"):
            console.rule("Multi-turn")
            summaries.append(
                run_multi_turn(
                    target,
                    logger,
                    rounds=multi_rounds,
                    use_llm_judge=use_llm,
                    campaigns=args.campaigns,
                )
            )

        if args.mode in ("all", "adaptive"):
            console.rule("Adaptive (attacker model)")
            summaries.append(
                run_adaptive(
                    target,
                    logger,
                    rounds=adaptive_rounds,
                    use_llm_judge=use_llm,
                    campaigns=args.campaigns,
                )
            )

    table = Table(title="Wyniki ASR (Attack Success Rate)")
    table.add_column("Mode")
    table.add_column("Total")
    table.add_column("Successes")
    table.add_column("ASR")
    for s in summaries:
        table.add_row(
            s["mode"],
            str(s["total"]),
            str(s["successes"]),
            f"{s['asr']:.1%}",
        )
    console.print(table)

    summary = {
        "target": settings.target_url,
        "hf_dataset": settings.hf_dataset,
        "repeats": repeats,
        "modes": summaries,
        "log_jsonl": str(logger.path),
        "owasp": "LLM01 Prompt Injection — see --mode checklist",
    }
    logger.write_summary(summary)
    console.print(f"[green]Logi tur: {logger.path}[/green]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
