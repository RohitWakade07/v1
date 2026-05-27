import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import verify_proof_signature
from app.models.models import (
    Assignment,
    GradingSession,
    ProofSubmission,
    SessionStatus,
    Student,
    UsedNonce,
)
from app.schemas.schemas import ProofSubmitRequest, ProofSubmitResponse


class ProofService:

    @staticmethod
    async def submit_proof(
        request: ProofSubmitRequest,
        current_student: Student,
        db: AsyncSession,
    ) -> ProofSubmitResponse:

        # ── 1. Cross-check student identity ──────────────────────────
        if request.student_id.upper() != current_student.roll_number.upper():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Proof student_id does not match authenticated student",
            )

        # ── 2. Replay prevention — nonce must be unused ───────────────
        nonce_result = await db.execute(
            select(UsedNonce).where(UsedNonce.nonce == request.nonce)
        )
        if nonce_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Proof nonce already used — replay detected",
            )

        # ── 3. Fetch and validate session ─────────────────────────────
        session_result = await db.execute(
            select(GradingSession).where(
                GradingSession.id == request.session_id,
                GradingSession.student_id == current_student.id,
            )
        )
        session: Optional[GradingSession] = session_result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        if session.status not in [SessionStatus.STARTED, SessionStatus.IN_PROGRESS]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is {session.status} — cannot accept proof",
            )

        # ── 4. Assignment match ───────────────────────────────────────
        if session.assignment_id != request.assignment_id:
            await ProofService._reject(
                session, db, "Assignment ID in proof does not match session"
            )
            return ProofSubmitResponse(
                session_id=session.id,
                status=SessionStatus.REJECTED,
                final_score=None,
                message="Assignment mismatch",
            )

        # ── 5. HMAC signature verification ───────────────────────────
        proof_dict = request.model_dump(mode="json")
        hmac_valid = verify_proof_signature(proof_dict, request.hmac_signature)
        if not hmac_valid:
            await ProofService._reject(
                session, db, "HMAC signature verification failed — proof tampered"
            )
            await ProofService._record_submission(
                request, session, db,
                hmac_valid=False, hashes_valid=False, score=None,
            )
            return ProofSubmitResponse(
                session_id=session.id,
                status=SessionStatus.REJECTED,
                final_score=None,
                message="Proof signature invalid",
            )

        # ── 6. SHA-256 output hash consistency check ──────────────────
        hashes_valid = ProofService._validate_hashes(request)
        if not hashes_valid:
            await ProofService._reject(
                session, db, "SHA-256 hash inconsistency detected in proof"
            )
            await ProofService._record_submission(
                request, session, db,
                hmac_valid=True, hashes_valid=False, score=None,
            )
            return ProofSubmitResponse(
                session_id=session.id,
                status=SessionStatus.REJECTED,
                final_score=None,
                message="Output hash verification failed",
            )

        # ── 7. Compute score ──────────────────────────────────────────
        assignment_result = await db.execute(
            select(Assignment).where(Assignment.id == request.assignment_id)
        )
        assignment: Assignment = assignment_result.scalar_one()
        final_score = ProofService._compute_score(request, assignment.max_score)

        # ── 8. Mark nonce used ────────────────────────────────────────
        db.add(UsedNonce(
            nonce=request.nonce,
            student_id=current_student.id,
        ))

        # ── 9. Complete session ───────────────────────────────────────
        now = datetime.now(timezone.utc)
        session.status = SessionStatus.COMPLETED
        session.submitted_at = now
        session.completed_at = now
        session.proof_nonce = request.nonce
        session.final_score = final_score
        session.score_breakdown = json.dumps({
            test_id: {
                "passed": r.passed,
                "score": r.score,
            }
            for test_id, r in request.results.items()
        })
        db.add(session)

        # ── 10. Immutable audit record ────────────────────────────────
        await ProofService._record_submission(
            request, session, db,
            hmac_valid=True, hashes_valid=True, score=final_score,
        )

        return ProofSubmitResponse(
            session_id=session.id,
            status=SessionStatus.COMPLETED,
            final_score=final_score,
            message=f"Proof verified. Score: {final_score:.1f} / {assignment.max_score}",
        )

    # ── Scoring ───────────────────────────────────────────────────────

    @staticmethod
    def _compute_score(request: ProofSubmitRequest, max_score: float) -> float:
        """
        Sum the per-test scores declared in the proof.
        Each test's score is already set by the grader binary;
        the backend trusts the structure but not the values —
        scores are re-bounded to [0, max_score].
        """
        total = sum(r.score for r in request.results.values() if r.passed)
        return round(min(total, max_score), 2)

    # ── Hash validation ───────────────────────────────────────────────

    @staticmethod
    def _validate_hashes(request: ProofSubmitRequest) -> bool:
        """
        Structural consistency checks on the proof hashes.
        - Every test result that claims passed=True must have a stdout_hash.
        - No hash field should be an empty string.
        - artifact_hashes values must be 64-char hex (SHA-256).
        """
        for test_id, result in request.results.items():
            if result.passed and not result.stdout_hash:
                return False
            if result.stdout_hash is not None and len(result.stdout_hash) == 0:
                return False

        for filename, hash_val in request.artifact_hashes.items():
            if not hash_val or len(hash_val) != 64:
                return False
            if not all(c in "0123456789abcdef" for c in hash_val.lower()):
                return False

        return True

    # ── Internal helpers ──────────────────────────────────────────────

    @staticmethod
    async def _reject(
        session: GradingSession,
        db: AsyncSession,
        reason: str,
    ) -> None:
        session.status = SessionStatus.REJECTED
        session.submitted_at = datetime.now(timezone.utc)
        session.rejection_reason = reason
        db.add(session)

    @staticmethod
    async def _record_submission(
        request: ProofSubmitRequest,
        session: GradingSession,
        db: AsyncSession,
        hmac_valid: bool,
        hashes_valid: bool,
        score: Optional[float],
    ) -> None:
        now = datetime.now(timezone.utc)
        record = ProofSubmission(
            session_id=session.id,
            student_id=session.student_id,
            assignment_id=session.assignment_id,
            nonce=request.nonce,
            grader_binary_hash=request.grader_binary_hash,
            raw_proof=json.dumps(request.model_dump(mode="json")),
            hmac_valid=hmac_valid,
            hashes_valid=hashes_valid,
            final_score=score,
            submitted_at=now,
            verified_at=now,
        )
        db.add(record)
