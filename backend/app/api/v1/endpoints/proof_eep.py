import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.core.security import decrypt_eep_file, parse_eep_report
from app.api.v1.dependencies import get_approved_student
from app.db.session import get_db
from app.models.models import (
    Assignment,
    FinalResult,
    GradingSession,
    ProofSubmission,
    SessionStatus,
    Student,
)
from app.schemas.schemas import ProofSubmitResponse, ErrorResponse
from app.services.eep_grading_service import (
    get_week_from_filename,
    grade_eep_checks,
    map_checks_to_results,
)

router = APIRouter(prefix="/proof", tags=["Proof EEP"])

_SUBMITTABLE_STATUSES = (
    SessionStatus.STARTED,
    SessionStatus.IN_PROGRESS,
    SessionStatus.RUNNING,
    SessionStatus.PROOF_GENERATED,
)


@router.post(
    "/submit-eep",
    response_model=ProofSubmitResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
    summary="Submit encrypted EEP verifier file (.eep1/.eep2/.eep3)",
)
async def submit_eep_proof(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    # Step 1 — size limit
    content = await file.read(settings.EEP_MAX_UPLOAD_BYTES + 1)
    if len(content) > settings.EEP_MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large (max {settings.EEP_MAX_UPLOAD_BYTES} bytes)",
        )

    # Step 2 — week from filename
    week = get_week_from_filename(file.filename or "")

    # Step 3 — decrypt
    try:
        plaintext = decrypt_eep_file(
            content.decode("utf-8", errors="replace"),
            settings.RSA_PRIVATE_KEY_PATH,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File is corrupted or tampered",
        )

    # Step 4 — parse report
    report = parse_eep_report(plaintext)
    if not report.get("student_id"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File is corrupted or tampered",
        )

    # Step 5 — student identity
    if report["student_id"].strip().upper() != current_student.roll_number.upper():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="student_id in file does not match your authenticated account",
        )

    # Step 6 — session
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id",
        )

    session_result = await db.execute(
        select(GradingSession).where(
            GradingSession.id == session_uuid,
            GradingSession.student_id == current_student.id,
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Step 7 — submittable state
    if session.status not in _SUBMITTABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not in a submittable state",
        )

    # Step 8 — assignment
    assignment_result = await db.execute(
        select(Assignment).where(Assignment.id == session.assignment_id)
    )
    assignment = assignment_result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    # Prefer filename week; fall back to WEEK: line in report if present
    report_week = report.get("week") or week
    if report_week not in ("1", "2", "3"):
        report_week = week

    # Step 9–10 — grade
    grading_result = grade_eep_checks(report.get("checks", []), report_week)
    _ = map_checks_to_results(report.get("checks", []), report_week)  # noqa: F841 — audit shape

    # Step 11 — serialise breakdown
    score_breakdown_str = json.dumps(grading_result["score_breakdown"])

    # Step 12 — update session
    now = datetime.utcnow()
    submission_nonce = str(uuid.uuid4())
    session.status = SessionStatus.VERIFIED
    session.final_score = grading_result["earned"]
    session.score_breakdown = score_breakdown_str
    session.submitted_at = now
    session.completed_at = now
    session.proof_nonce = submission_nonce

    # Step 13 — final result
    final_result = FinalResult(
        session_id=session.id,
        student_id=current_student.id,
        assignment_id=assignment.id,
        score=grading_result["earned"],
        passed=grading_result["passed"],
        score_breakdown=score_breakdown_str,
        verified_at=now,
    )

    # Step 14 — audit record
    proof_record = ProofSubmission(
        session_id=session.id,
        student_id=current_student.id,
        assignment_id=assignment.id,
        nonce=submission_nonce,
        grader_binary_hash="eep-verifier-script",
        raw_proof=plaintext,
        hmac_valid=True,
        hashes_valid=True,
        final_score=grading_result["earned"],
        verified_at=now,
    )

    db.add(session)
    db.add(final_result)
    db.add(proof_record)
    await db.flush()

    earned = grading_result["earned"]
    total = grading_result["total"]
    pct = grading_result["score_pct"]

    return ProofSubmitResponse(
        session_id=session.id,
        status=SessionStatus.VERIFIED,
        final_score=earned,
        message=f"EEP submission verified — score: {earned}/{total} ({pct}%)",
    )
