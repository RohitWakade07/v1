import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db
from app.core.security import hash_password

# ── In-memory SQLite for tests ────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest_asyncio.fixture
async def registered_student(client: AsyncClient):
    resp = await client.post("/api/v1/auth/student/register", json={
        "roll_number": "22BEC001",
        "full_name": "Test Student",
        "email": "test@example.com",
        "password": "securepass123",
    })
    assert resp.status_code == 201
    return resp.json()


# ── Auth tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_student_register(client: AsyncClient):
    resp = await client.post("/api/v1/auth/student/register", json={
        "roll_number": "22bec001",
        "full_name": "Alice",
        "email": "alice@example.com",
        "password": "password123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["roll_number"] == "22BEC001"  # uppercased


@pytest.mark.asyncio
async def test_student_login_success(client: AsyncClient, registered_student):
    resp = await client.post("/api/v1/auth/student/login", json={
        "roll_number": "22BEC001",
        "password": "securepass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "student"


@pytest.mark.asyncio
async def test_student_login_wrong_password(client: AsyncClient, registered_student):
    resp = await client.post("/api/v1/auth/student/login", json={
        "roll_number": "22BEC001",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_registration(client: AsyncClient, registered_student):
    resp = await client.post("/api/v1/auth/student/register", json={
        "roll_number": "22BEC001",
        "full_name": "Duplicate",
        "email": "dup@example.com",
        "password": "password123",
    })
    assert resp.status_code == 409


# ── Session tests ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_session_unauthenticated(client: AsyncClient):
    resp = await client.post("/api/v1/session/create", json={
        "assignment_id": "00000000-0000-0000-0000-000000000001"
    })
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
