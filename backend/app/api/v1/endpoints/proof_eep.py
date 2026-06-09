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
    SessionStatus.CREATED,
    SessionStatus.CHALLENGE_ISSUED,
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

    # Step 7a — Check pending payload
    if not session.pending_payload:
        session.status = SessionStatus.FAILED
        session.rejection_reason = "No evaluator payload was received for this session. Did you run the CLI tool?"
        db.add(session)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No evaluator payload was received for this session. Please run the evaluator tool first.",
        )

    try:
        pending_plaintext = decrypt_eep_file(
            session.pending_payload,
            settings.RSA_PRIVATE_KEY_PATH,
        )
        pending_report = parse_eep_report(pending_plaintext)
    except Exception:
        pending_report = None

    is_valid = True
    rejection_reason = None

    if not pending_report:
        is_valid = False
        rejection_reason = "Saved evaluator payload is corrupted or invalid."
    else:
        # Compare session_id
        if str(report.get("session_id", "")).strip() != str(pending_report.get("session_id", "")).strip():
            is_valid = False
            rejection_reason = f"Session ID in proof ({report.get('session_id')}) does not match session payload ({pending_report.get('session_id')})."
        # Compare student_id
        elif str(report.get("student_id", "")).strip().upper() != str(pending_report.get("student_id", "")).strip().upper():
            is_valid = False
            rejection_reason = "Student ID in proof does not match session payload."
        # Compare checks
        else:
            checks_a = report.get("checks", [])
            checks_b = pending_report.get("checks", [])
            if len(checks_a) != len(checks_b):
                is_valid = False
                rejection_reason = "Number of checks in proof does not match evaluator payload."
            else:
                for c_a, c_b in zip(checks_a, checks_b):
                    if c_a.get("id") != c_b.get("id") or c_a.get("passed") != c_b.get("passed") or c_a.get("score") != c_b.get("score"):
                        is_valid = False
                        rejection_reason = "Check results in proof do not match evaluator payload."
                        break

    if not is_valid:
        session.status = SessionStatus.FAILED
        session.rejection_reason = rejection_reason
        db.add(session)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Verification failed: {rejection_reason}",
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
