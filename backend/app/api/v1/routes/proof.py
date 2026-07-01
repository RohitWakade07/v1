import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.v1.dependencies import get_approved_student_ratelimited
from app.core.config import settings
from app.core.security import decrypt_eep_file, parse_eep_report
from app.db.session import get_db
from app.models.models import (
    Assignment,
    Certificate,
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
from app.core.cache import invalidate as cache_invalidate, session_cache_key

router = APIRouter(prefix="/proof", tags=["Proof"])





@router.post(
    "/submit-eep",
    response_model=ProofSubmitResponse,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
    summary="Submit encrypted EEP verifier report (.eep1/.eep2/.eep3)",
)
async def submit_eep_proof(
    session_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    current_student: Student = Depends(get_approved_student_ratelimited),
    db: AsyncSession = Depends(get_db),
):
    filename = file.filename or ""
    lower = filename.lower()
    if not any(lower.endswith(ext) for ext in (".eep1", ".eep2", ".eep3")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_FILE_TYPE", "message": "File must be .eep1, .eep2, or .eep3"},
        )

    raw = (await file.read()).decode("utf-8", errors="replace").strip()
    if len(raw.encode("utf-8")) > settings.EEP_MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "FILE_TOO_LARGE", "message": f"EEP file exceeds {settings.EEP_MAX_UPLOAD_BYTES} bytes"},
        )

    session = (
        await db.execute(
            select(GradingSession).where(
                GradingSession.id == session_id,
                GradingSession.student_id == current_student.id,
            )
        )
    ).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.status not in (
        SessionStatus.CREATED,
        SessionStatus.CHALLENGE_ISSUED,
        SessionStatus.RUNNING,
        SessionStatus.PROOF_GENERATED,
        SessionStatus.STARTED,
        SessionStatus.IN_PROGRESS,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session is {session.status} — cannot accept EEP submission",
        )

    assignment = (
        await db.execute(select(Assignment).where(Assignment.id == session.assignment_id))
    ).scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    try:
        plaintext = decrypt_eep_file(raw, settings.RSA_PRIVATE_KEY_PATH)
    except (ValueError, FileNotFoundError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "DECRYPT_FAILED", "message": str(exc)},
        ) from exc

    report = parse_eep_report(plaintext)
    report_week = get_week_from_filename(filename)
    grading_result = grade_eep_checks(report.get("checks", []), report_week)
    _ = map_checks_to_results(report.get("checks", []), report_week)

    final_score = round(min(grading_result["earned"], assignment.max_score), 2)
    max_score = grading_result["total"]
    now = datetime.utcnow()
    passed = final_score >= (max_score * 0.4)

    session.status = SessionStatus.VERIFIED
    session.submitted_at = now
    session.completed_at = now
    session.final_score = final_score
    session.score_breakdown = json.dumps(grading_result.get("score_breakdown", {}))
    db.add(session)

    final_result = FinalResult(
        session_id=session.id,
        student_id=current_student.id,
        assignment_id=assignment.id,
        score=final_score,
        passed=passed,
        score_breakdown=session.score_breakdown,
        verified_at=now,
    )
    db.add(final_result)
    await db.flush()

    if passed:
        cert_code = (
            f"CERT-{assignment.slug.upper()}-{current_student.roll_number.upper()}-"
            f"{uuid.uuid4().hex[:5].upper()}"
        )
        db.add(
            Certificate(
                student_id=current_student.id,
                assignment_id=assignment.id,
                final_result_id=final_result.id,
                certificate_code=cert_code,
                issued_at=now,
            )
        )

    db.add(
        ProofSubmission(
            session_id=session.id,
            student_id=current_student.id,
            assignment_id=assignment.id,
            nonce=f"eep-{session.id}-{now.timestamp()}",
            grader_binary_hash="eep-verifier",
            raw_proof=plaintext[:10000],
            hmac_valid=True,
            hashes_valid=True,
            final_score=final_score,
            submitted_at=now,
            verified_at=now,
        )
    )
    await db.commit()
    await cache_invalidate(session_cache_key(session_id, current_student.id))

    return ProofSubmitResponse(
        session_id=session.id,
        status=SessionStatus.VERIFIED,
        final_score=final_score,
        message=f"EEP verified. Score: {final_score}/{max_score}",
    )
