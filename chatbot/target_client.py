"""HTTP client for the target pancake chatbot."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx

from config import settings
from rate_limit import RateLimiter

logger = logging.getLogger(__name__)


@dataclass
class ChatResponse:
    chat_id: str
    reply: str
    raw: dict


class TargetClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        max_qpm: int | None = None,
    ) -> None:
        self.url = base_url or settings.target_url
        self.timeout = timeout or settings.request_timeout
        self._client = httpx.Client(timeout=self.timeout)
        qpm = max_qpm if max_qpm is not None else settings.max_qpm
        self._limiter = RateLimiter(max_calls=qpm, period_sec=60.0)
        self._max_retries = 3

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TargetClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def chat(self, message: str, chat_id: str | None = None) -> ChatResponse:
        payload: dict = {"message": message}
        if chat_id:
            payload["chat_id"] = chat_id

        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            waited = self._limiter.wait()
            if waited > 0.5:
                logger.info("Rate limit: czekano %.1fs (max %s/min)", waited, self._limiter.max_calls)
            try:
                response = self._client.post(self.url, json=payload)
                if response.status_code >= 500 and attempt < self._max_retries:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                response.raise_for_status()
                data = response.json()
                return ChatResponse(
                    chat_id=str(data.get("chat_id") or ""),
                    reply=str(data.get("reply") or data.get("response") or ""),
                    raw=data,
                )
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if exc.response is not None and exc.response.status_code >= 500:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                raise
            except httpx.HTTPError as exc:
                last_exc = exc
                time.sleep(min(2 ** attempt, 8))
        assert last_exc is not None
        raise last_exc

    def healthcheck(self) -> bool:
        try:
            probe = self.chat("cześć")
            return bool(probe.reply)
        except Exception:
            return False
