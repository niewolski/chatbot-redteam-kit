"""Gemini helper for attacker and judge models."""

from __future__ import annotations

from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings


class GeminiClient:
    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.attacker_model
        self._client = genai.Client(api_key=settings.gemini_api_key)

    @retry(wait=wait_exponential(min=1, max=20), stop=stop_after_attempt(4), reraise=True)
    def generate(self, prompt: str, system: str | None = None) -> str:
        contents = prompt
        config = None
        if system:
            from google.genai import types

            config = types.GenerateContentConfig(system_instruction=system)
        response = self._client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError(f"Pusta odpowiedź z modelu {self.model}")
        return text


def attacker_client() -> GeminiClient:
    return GeminiClient(settings.attacker_model)


def judge_client() -> GeminiClient:
    return GeminiClient(settings.judge_model)
