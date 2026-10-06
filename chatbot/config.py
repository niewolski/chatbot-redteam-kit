"""Configuration loaded from chatbot/.env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def _env(*keys: str, default: str | None = None) -> str | None:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value.strip()
    return default


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    attacker_model: str
    judge_model: str
    target_url: str
    hf_dataset: str
    hf_split: str
    hf_text_column: str
    repeats: int
    max_prompts: int
    max_qpm: int
    multi_turn_rounds: int
    adaptive_rounds: int
    request_timeout: float
    logs_dir: Path

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = _env("GEMINI-API", "GEMINI_API", "GEMINI_API_KEY", "GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Brak klucza Gemini. Ustaw GEMINI-API w chatbot/.env "
                "(wzór: chatbot/.env.template)."
            )
        return cls(
            gemini_api_key=api_key,
            attacker_model=_env(
                "GEMINI-MODEL-ATTACKER",
                "GEMINI_MODEL_ATTACKER",
                default="gemini-2.0-flash",
            )
            or "gemini-2.0-flash",
            judge_model=_env(
                "GEMINI-MODEL-JUDGE",
                "GEMINI_MODEL_JUDGE",
                default="gemini-2.0-flash",
            )
            or "gemini-2.0-flash",
            target_url=_env("TARGET_URL", default="http://localhost:8080/chat")
            or "http://localhost:8080/chat",
            hf_dataset=_env(
                "HF_DATASET",
                default="deepset/prompt-injections",
            )
            or "deepset/prompt-injections",
            hf_split=_env("HF_SPLIT", default="train") or "train",
            hf_text_column=_env("HF_TEXT_COLUMN", default="text") or "text",
            # Lepiej więcej unikalnych ataków × mniej powtórzeń niż 20×15 tego samego
            repeats=int(_env("REPEATS", default="5") or "5"),
            max_prompts=int(_env("MAX_PROMPTS", default="100") or "100"),
            max_qpm=int(_env("MAX_QPM", default="15") or "15"),
            multi_turn_rounds=int(_env("MULTI_TURN_ROUNDS", default="5") or "5"),
            adaptive_rounds=int(_env("ADAPTIVE_ROUNDS", default="8") or "8"),
            request_timeout=float(_env("REQUEST_TIMEOUT", default="60") or "60"),
            logs_dir=ROOT / "logs",
        )


settings = Settings.from_env()
