"""Redis INCR + TTL rate limiting helpers."""

from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.db.redis import get_redis, rate_limit_key


async def check_rate_limit(
    identifier: str,
    action: str,
    *,
    limit: int,
    window_seconds: int = 60,
) -> None:
    """Increment a Redis counter and raise 429 when over *limit* within *window_seconds*."""
    redis = await get_redis()
    key = rate_limit_key(identifier, action)
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window_seconds)
    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RATE_LIMITED",
                "message": f"Too many requests. Try again in {window_seconds} seconds.",
            },
        )


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"
