"""JSONL + console logging for every red-team turn."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import settings


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunLogger:
    def __init__(self, run_name: str | None = None) -> None:
        settings.logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = run_name or f"redteam_{stamp}"
        self.path = settings.logs_dir / f"{name}.jsonl"
        self.summary_path = settings.logs_dir / f"{name}_summary.json"
        self._logger = logging.getLogger("redteam")
        self.events: list[dict[str, Any]] = []

        fh = logging.FileHandler(settings.logs_dir / f"{name}.log", encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        self._logger.setLevel(logging.INFO)
        if not self._logger.handlers:
            self._logger.addHandler(fh)
            sh = logging.StreamHandler()
            sh.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(sh)

    def log_turn(self, event: dict[str, Any]) -> None:
        record = {"ts": utc_now(), **event}
        self.events.append(record)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        mode = event.get("mode", "?")
        broken = event.get("judgment", {}).get("broken")
        prompt_preview = (event.get("attack") or "")[:80].replace("\n", " ")
        self._logger.info(
            "[%s] broken=%s prompt=%r",
            mode,
            broken,
            prompt_preview,
        )

    def write_summary(self, summary: dict[str, Any]) -> Path:
        payload = {"ts": utc_now(), **summary}
        self.summary_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._logger.info("Podsumowanie: %s", self.summary_path)
        return self.summary_path
