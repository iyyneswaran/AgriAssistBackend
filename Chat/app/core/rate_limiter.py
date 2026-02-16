import time
from fastapi import Request, HTTPException, status
from collections import defaultdict
from app.core.config import settings

RATE_LIMIT = 60  # requests per minute
WINDOW_SIZE = 60  # seconds

_request_log = defaultdict(list)


def rate_limit_dependency(request: Request):
    client = request.client
    identifier = client.host if client else "unknown"

    now = time.time()
    window_start = now - WINDOW_SIZE

    _request_log[identifier] = [
        timestamp for timestamp in _request_log[identifier]
        if timestamp > window_start
    ]

    if len(_request_log[identifier]) >= RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )

    _request_log[identifier].append(now)
