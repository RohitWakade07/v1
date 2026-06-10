import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.core.config import settings
from tests.conftest import TestSession


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
    resp = await client.post("/api/v1/sessions", json={
        "assignment_id": str(uuid.uuid4())
    })
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_session_assignment_not_found(client):
    token = await register_and_login(client, roll="22BEC100")
    
    from app.models.models import Student, Mentor, Classroom, ClassroomEnrollment
    from app.core.security import hash_password
    from sqlmodel import select
    async with TestSession() as db:
        res = await db.execute(select(Student).where(Student.roll_number == "22BEC100"))
        student = res.scalar_one()
        
        mentor = Mentor(
            username="prof_not_found", full_name="Prof", email="prof_nf@test.com",
            hashed_password=hash_password("pass"),
        )
        db.add(mentor)
        await db.flush()
        
        classroom = Classroom(
            name="Test Class", class_code="CLASS-NF", mentor_id=mentor.id
        )
        db.add(classroom)
        await db.flush()
        
        db.add(ClassroomEnrollment(
            classroom_id=classroom.id,
            student_id=student.id,
            status="APPROVED"
        ))
        await db.commit()

    resp = await client.post(
        "/api/v1/sessions",
        json={"assignment_id": str(uuid.uuid4())},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_challenge_package_retrieval(client):
    from app.models.models import Mentor, Assignment, AssignmentCategory, AssignmentConfig, Classroom, ClassroomEnrollment, Student
    from app.core.security import hash_password
    from sqlmodel import select

    token = await register_and_login(client, roll="22BEC002")

    async with TestSession() as db:
        res = await db.execute(select(Student).where(Student.roll_number == "22BEC002"))
        student = res.scalar_one()

        mentor = Mentor(
            username="prof2", full_name="Prof Two", email="prof2@test.com",
            hashed_password=hash_password("pass"),
        )
        db.add(mentor)
        await db.flush()
        
        classroom = Classroom(
            name="Test Class 2", class_code="CLASS-2", mentor_id=mentor.id
        )
        db.add(classroom)
        await db.flush()
        
        db.add(ClassroomEnrollment(
            classroom_id=classroom.id,
            student_id=student.id,
            status="APPROVED"
        ))
        
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

    sess_resp = await client.post(
        "/api/v1/sessions",
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

