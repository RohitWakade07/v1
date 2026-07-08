from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        from sqlalchemy import text
        try:
            await conn.execute(text("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS mentor_score FLOAT;"))
            await conn.execute(text("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS mentor_feedback TEXT;"))
            await conn.execute(text("ALTER TABLE proof_submissions DROP COLUMN IF EXISTS hmac_valid;"))
            await conn.execute(text("DROP TABLE IF EXISTS evaluator_builds CASCADE;"))
        except Exception:
            pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
