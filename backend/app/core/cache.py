"""Lightweight Redis cache-aside helpers (uses app Redis DB 0)."""

import json
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

from app.db.redis import get_redis

T = TypeVar("T")

# TTL constants (seconds)
TTL_ASSIGNMENT = 300   # 5 min
TTL_CLASSROOM = 300    # 5 min
TTL_SESSION = 300      # 5 min
TTL_PROFILE = 120      # 2 min

CACHE_PREFIX = "cache:"


def _serialize(value: Any) -> str:
    if isinstance(value, Enum):
        return json.dumps(value.value)
    if isinstance(value, datetime):
        return json.dumps(value.isoformat())
    if hasattr(value, "model_dump"):
        return json.dumps(value.model_dump(mode="json"))
    if isinstance(value, uuid.UUID):
        return json.dumps(str(value))
    return json.dumps(value, default=str)


def cache_key(entity: str, *parts: str) -> str:
    return f"{CACHE_PREFIX}{entity}:{':'.join(parts)}"


async def get_or_set(
    key: str,
    fetch_fn: Callable[[], Awaitable[T]],
    ttl: int,
) -> T:
    """Cache-aside: return cached JSON value or call *fetch_fn* and store."""
    redis = await get_redis()
    cached = await redis.get(key)
    if cached is not None:
        return json.loads(cached)

    value = await fetch_fn()
    await redis.setex(key, ttl, _serialize(value))
    return value


async def invalidate(key: str) -> None:
    redis = await get_redis()
    await redis.delete(key)


async def invalidate_prefix(prefix: str) -> None:
    """Delete all keys matching ``cache:<prefix>*``."""
    redis = await get_redis()
    full_prefix = f"{CACHE_PREFIX}{prefix}"
    cursor = 0
    while True:
        cursor, keys = await redis.scan(cursor, match=f"{full_prefix}*", count=100)
        if keys:
            await redis.delete(*keys)
        if cursor == 0:
            break


def assignment_cache_key(assignment_id: uuid.UUID) -> str:
    return cache_key("assignment", str(assignment_id))


def session_cache_key(session_id: uuid.UUID, student_id: uuid.UUID | None = None) -> str:
    if student_id is not None:
        return cache_key("session", str(session_id), str(student_id))
    return cache_key("session", str(session_id))


def classroom_cache_key(classroom_id: uuid.UUID) -> str:
    return cache_key("classroom", str(classroom_id))


def student_profile_cache_key(student_id: uuid.UUID) -> str:
    return cache_key("profile", "student", str(student_id))
