import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.main import app
from app.db.session import get_db
from app.core.config import settings
from app.db.redis import close_redis

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


# ── Helpers ───────────────────────────────────────────────────────────

async def register_and_login(client, roll="22BEC001", password="password123"):
    await client.post("/api/v1/auth/student/register", json={
        "roll_number": roll,
        "full_name": "Test Student",
        "email": f"{roll.lower()}@test.com",
        "password": password,
    })
    resp = await client.post("/api/v1/auth/student/login", json={
        "roll_number": roll,
        "password": password,
    })
    return resp.json()["access_token"]


def make_proof(session_id, assignment_id, student_id="22BEC001", nonce=None):
    nonce = nonce or str(uuid.uuid4())
    payload = {
        "session_id": str(session_id),
        "assignment_id": str(assignment_id),
        "student_id": student_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nonce": nonce,
        "grader_binary_hash": "a" * 64,
        "results": {
            "test_1": {
                "test_id": "test_1",
                "passed": True,
                "stdout_hash": "b" * 64,
                "stderr_hash": None,
                "exit_code": 0,
                "score": 50.0,
            }
        },
        "artifact_hashes": {"output.txt": "c" * 64},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    sig = hmac.new(
        settings.PROOF_SIGNING_KEY.encode(),
        canonical.encode(),
        hashlib.sha256,
    ).hexdigest()
    payload["hmac_signature"] = sig
    return payload


# ── Auth tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_normalises_roll(client):
    resp = await client.post("/api/v1/auth/student/register", json={
        "roll_number": "22bec001",
        "full_name": "Alice",
        "email": "alice@test.com",
        "password": "password123",
    })
    assert resp.status_code == 201
    assert resp.json()["roll_number"] == "22BEC001"


@pytest.mark.asyncio
async def test_login_success(client):
    token = await register_and_login(client)
    assert len(token) > 10


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await register_and_login(client)
    resp = await client.post("/api/v1/auth/student/login", json={
        "roll_number": "22BEC001", "password": "wrong"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_registration(client):
    await register_and_login(client)
    resp = await client.post("/api/v1/auth/student/register", json={
        "roll_number": "22BEC001",
        "full_name": "Dup",
        "email": "dup@test.com",
        "password": "password123",
    })
    assert resp.status_code == 409


# ── Session tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_session_requires_auth(client):
    resp = await client.post("/api/v1/sessions/", json={
        "assignment_id": str(uuid.uuid4())
    })
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_session_assignment_not_found(client):
    token = await register_and_login(client)
    resp = await client.post(
        "/api/v1/sessions/",
        json={"assignment_id": str(uuid.uuid4())},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ── Proof tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_proof_replay_rejected(client):
    from app.models.models import Mentor, Assignment, AssignmentCategory
    from app.core.security import hash_password
    from app.db.session import get_db as real_get_db

    async with TestSession() as db:
        mentor = Mentor(
            username="prof1", full_name="Prof", email="prof@test.com",
            hashed_password=hash_password("pass"),
        )
        db.add(mentor)
        await db.flush()
        assignment = Assignment(
            slug="week1", title="Week 1", category=AssignmentCategory.ARTIFACT_VALIDATION,
            is_published=True, created_by_id=mentor.id,
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        assignment_id = assignment.id

    token = await register_and_login(client)
    sess_resp = await client.post(
        "/api/v1/sessions/",
        json={"assignment_id": str(assignment_id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sess_resp.status_code == 201
    session_id = sess_resp.json()["session_id"]

    nonce = str(uuid.uuid4())
    proof = make_proof(session_id, assignment_id, nonce=nonce)

    r1 = await client.post(
        "/api/v1/proof/submit",
        json=proof,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 200
    assert r1.json()["status"] == "VERIFIED"

    r2 = await client.post(
        "/api/v1/proof/submit",
        json=proof,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_challenge_package_retrieval(client):
    from app.models.models import Mentor, Assignment, AssignmentCategory, AssignmentConfig
    from app.core.security import hash_password

    async with TestSession() as db:
        mentor = Mentor(
            username="prof2", full_name="Prof Two", email="prof2@test.com",
            hashed_password=hash_password("pass"),
        )
        db.add(mentor)
        await db.flush()
        assignment = Assignment(
            slug="week2", title="Week 2", category=AssignmentCategory.ARTIFACT_VALIDATION,
            is_published=True, created_by_id=mentor.id,
        )
        db.add(assignment)
        await db.flush()
        
        # Add assignment config
        config = AssignmentConfig(
            assignment_id=assignment.id,
            config_data='{"validation_rules": [{"rule_id": "test_1", "type": "file_exists", "target": "output.txt", "points": 50.0}]}'
        )
        db.add(config)
        await db.commit()
        await db.refresh(assignment)
        assignment_id = assignment.id

    token = await register_and_login(client, roll="22BEC002")
    sess_resp = await client.post(
        "/api/v1/sessions/",
        json={"assignment_id": str(assignment_id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sess_resp.status_code == 201
    session_id = sess_resp.json()["session_id"]

    challenge_resp = await client.get(
        f"/api/v1/sessions/{session_id}/challenge",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert challenge_resp.status_code == 200
    data = challenge_resp.json()
    assert data["session"]["session_id"] == session_id
    assert data["session"]["nonce"] is not None
    assert len(data["validation_rules"]) == 1
    assert data["validation_rules"][0]["rule_id"] == "test_1"


@pytest.mark.asyncio
async def test_proof_generates_result_and_certificate(client):
    from app.models.models import Mentor, Assignment, AssignmentCategory, FinalResult, Certificate
    from app.core.security import hash_password
    from sqlmodel import select

    async with TestSession() as db:
        mentor = Mentor(
            username="prof3", full_name="Prof Three", email="prof3@test.com",
            hashed_password=hash_password("pass"),
        )
        db.add(mentor)
        await db.flush()
        assignment = Assignment(
            slug="week3", title="Week 3", category=AssignmentCategory.ARTIFACT_VALIDATION,
            is_published=True, created_by_id=mentor.id, max_score=100.0,
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        assignment_id = assignment.id

    token = await register_and_login(client, roll="22BEC003")
    sess_resp = await client.post(
        "/api/v1/sessions/",
        json={"assignment_id": str(assignment_id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sess_resp.status_code == 201
    session_id = sess_resp.json()["session_id"]

    nonce = str(uuid.uuid4())
    proof = make_proof(session_id, assignment_id, student_id="22BEC003", nonce=nonce)

    submit_resp = await client.post(
        "/api/v1/proof/submit",
        json=proof,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "VERIFIED"

    # Verify that a FinalResult and Certificate were generated in the DB
    async with TestSession() as db:
        res_stmt = select(FinalResult).where(FinalResult.session_id == uuid.UUID(session_id))
        result = (await db.execute(res_stmt)).scalar_one_or_none()
        assert result is not None
        assert result.score == 50.0
        assert result.passed is True

        cert_stmt = select(Certificate).where(Certificate.student_id == result.student_id)
        certificate = (await db.execute(cert_stmt)).scalar_one_or_none()
        assert certificate is not None
        assert certificate.final_result_id == result.id
        assert certificate.certificate_code.startswith("CERT-WEEK3-22BEC003-")

