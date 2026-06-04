"""Shared pytest fixtures for backend API tests."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.db.redis import close_redis
from app.db.session import get_db
from app.main import app

TEST_DB = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB, echo=False)
TestSession = sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as s:
        try:
            yield s
            await s.commit()
        except Exception:
            await s.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def cleanup_redis():
    from app.db.redis import get_redis

    try:
        r = await get_redis()
        await r.flushdb()
    except Exception:
        pass
    yield
    try:
        r = await get_redis()
        await r.flushdb()
    except Exception:
        pass
    await close_redis()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
