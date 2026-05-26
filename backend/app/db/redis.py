import redis.asyncio as aioredis
from app.core.config import settings

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


# Key helpers — centralised so typos don't create ghost keys
def session_heartbeat_key(session_id: str) -> str:
    """TTL key — expires if no heartbeat arrives within timeout window."""
    return f"heartbeat:ttl:{session_id}"


def session_sequence_key(session_id: str) -> str:
    """Tracks the last accepted heartbeat sequence number."""
    return f"heartbeat:seq:{session_id}"


def rate_limit_key(identifier: str, action: str) -> str:
    return f"ratelimit:{action}:{identifier}"
