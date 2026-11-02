"""Small in-memory sliding-window rate limiter (per client IP) for AI endpoints."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from .config import get_settings

_hits: dict[str, deque] = defaultdict(deque)


def ai_rate_limit(request: Request) -> None:
    limit = get_settings().rate_limit_per_minute
    key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window = _hits[key]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= limit:
        raise HTTPException(status_code=429, detail="Too many AI requests; try again in a minute.")
    window.append(now)


def reset() -> None:
    _hits.clear()
