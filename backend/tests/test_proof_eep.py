"""Integration tests for POST /api/v1/proof/submit-eep (mocked decryption)."""

import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.models.models import (
    Assignment,
    AssignmentCategory,
    Classroom,
    ClassroomEnrollment,
    Mentor,
    SessionStatus,
)
from app.core.security import hash_password
from tests.conftest import TestSession
from tests.test_backend import register_and_login


SAMPLE_PLAINTEXT = """STUDENT_ID: 22BEC010
TIMESTAMP: 2026-06-04T12:00:00Z
dir:week-01: PASS
dir:week-02: PASS
dir:week-03: PASS
dir:week-04: PASS
dir:week-05: PASS
dir:week-06: PASS
dir:week-07: PASS
dir:week-08: PASS
dir:week-09: PASS
dir:week-10: PASS
dir:week-11: PASS
dir:week-12: PASS
dir:week-13: PASS
dir:week-14: PASS
dir:week-15: PASS
dir:week-16: PASS
dir:week-17: PASS
dir:week-18: PASS
dir:week-19: PASS
dir:week-20: PASS
dir:notes: PASS
dir:scripts: PASS
dir:capstone: PASS
readme:week-01: PASS
bashrc: PASS
workspace-report: PASS
Overall: PASS
"""

FAKE_BLOB = "fakekey:fakebody"


@pytest.mark.asyncio
async def test_submit_eep_verified(client: AsyncClient):
    roll = "22BEC010"
    async with TestSession() as db:
        mentor = Mentor(
            username="eep_mentor",
            full_name="EEP Mentor",
            email="eep_mentor@test.com",
            hashed_password=hash_password("pass"),
        )
        db.add(mentor)
        await db.flush()

        classroom = Classroom(
            name="EEP Class",
            class_code="EEP-TEST01",
            mentor_id=mentor.id,
        )
        db.add(classroom)
        await db.flush()

        assignment = Assignment(
            slug="eep-week1",
            title="EEP Week 1",
            category=AssignmentCategory.MANUAL_REVIEW,
            is_published=True,
            created_by_id=mentor.id,
            max_score=40.0,
        )
        db.add(assignment)
        await db.flush()

        from app.models.models import Student

        student = Student(
            roll_number=roll,
            full_name="EEP Student",
            email=f"{roll.lower()}@test.com",
            hashed_password=hash_password("password123"),
        )
        db.add(student)
        await db.flush()

        db.add(
            ClassroomEnrollment(
                classroom_id=classroom.id,
                student_id=student.id,
                status="APPROVED",
            )
        )

        from app.models.models import GradingSession

        session = GradingSession(
            student_id=student.id,
            assignment_id=assignment.id,
            status=SessionStatus.STARTED,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        session_id = session.id

    token = await register_and_login(client, roll=roll, password="password123")

    with patch("app.api.v1.endpoints.proof_eep.decrypt_eep_file", return_value=SAMPLE_PLAINTEXT):
        files = {"file": ("TEST_EEP1_Week1.eep1", FAKE_BLOB, "application/octet-stream")}
        data = {"session_id": str(session_id)}
        resp = await client.post(
            "/api/v1/proof/submit-eep",
            data=data,
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "VERIFIED"
    assert body["final_score"] == 37.0
    assert "37.0/40" in body["message"]

    from app.models.models import FinalResult, ProofSubmission, GradingSession
    from sqlmodel import select

    async with TestSession() as db:
        gs = (
            await db.execute(
                select(GradingSession).where(GradingSession.id == session_id)
            )
        ).scalar_one()
        assert gs.status == SessionStatus.VERIFIED

        fr = (
            await db.execute(
                select(FinalResult).where(FinalResult.session_id == session_id)
            )
        ).scalar_one_or_none()
        assert fr is not None
        assert fr.passed is True

        ps = (
            await db.execute(
                select(ProofSubmission).where(ProofSubmission.session_id == session_id)
            )
        ).scalar_one_or_none()
        assert ps is not None
        assert ps.hmac_valid is True
        assert ps.grader_binary_hash == "eep-verifier-script"
