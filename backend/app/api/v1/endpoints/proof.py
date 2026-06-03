from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import Student
from app.api.v1.dependencies import get_current_student, get_approved_student
from app.services.proof_service import ProofService
from app.schemas.schemas import (
    ProofSubmitRequest,
    ProofSubmitResponse,
    ErrorResponse,
)

router = APIRouter(prefix="/proof", tags=["Proof Submission"])


@router.post(
    "/submit",
    response_model=ProofSubmitResponse,
    responses={
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
    summary="Submit signed proof file after local grading completes",
)
async def submit_proof(
    body: ProofSubmitRequest,
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    """
    The grader binary calls this automatically on completion.

    Verification steps performed server-side:
    1. student_id in proof matches authenticated JWT
    2. nonce has never been used before (replay prevention)
    3. session exists and is in a submittable state
    4. assignment_id matches the session
    5. HMAC-SHA256 signature re-derived and compared
    6. SHA-256 output hash structural consistency checked
    7. score computed from verified test results
    """
    return await ProofService.submit_proof(body, current_student, db)
