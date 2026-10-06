"""Simple sliding-window rate limiter for target chatbot calls."""

from __future__ import annotations

import threading
import time
from collections import deque


class RateLimiter:
    """Max `max_calls` requests in any rolling `period_sec` window."""

    def __init__(self, max_calls: int = 15, period_sec: float = 60.0) -> None:
        self.max_calls = max(1, max_calls)
        self.period_sec = period_sec
        self._times: deque[float] = deque()
        self._lock = threading.Lock()

    def wait(self) -> float:
        """Block until a slot is free. Returns seconds waited."""
        waited = 0.0
        while True:
            with self._lock:
                now = time.monotonic()
                while self._times and now - self._times[0] >= self.period_sec:
                    self._times.popleft()
                if len(self._times) < self.max_calls:
                    self._times.append(now)
                    return waited
                sleep_for = self.period_sec - (now - self._times[0]) + 0.05
            time.sleep(max(sleep_for, 0.05))
            waited += max(sleep_for, 0.05)
