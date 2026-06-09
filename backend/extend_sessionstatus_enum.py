import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

_NEW_SESSION_STATUSES = (
    "CREATED",
    "CHALLENGE_ISSUED",
    "RUNNING",
    "ABORTED",
    "PROOF_GENERATED",
    "PROOF_SUBMITTED",
    "VERIFIED",
    "FAILED",
)


async def extend_enum() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        for value in _NEW_SESSION_STATUSES:
            # PostgreSQL does not allow parameterized enum labels in ALTER TYPE.
            await conn.execute(
                text(f"ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS '{value}'")
            )
    await engine.dispose()
    print("SessionStatus enum updated.")


if __name__ == "__main__":
    asyncio.run(extend_enum())
