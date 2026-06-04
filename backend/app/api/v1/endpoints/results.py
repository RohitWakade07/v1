import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.session import get_db
from app.models.models import (
    GradingSession,
    SessionStatus,
    Student,
    Assignment,
    COMPLETED_RESULT_STATUSES,
)
from app.api.v1.dependencies import get_current_student
from app.schemas.schemas import ErrorResponse

router = APIRouter(prefix="/results", tags=["Results"])


# BUG FIX: Results endpoints were returning raw dicts with no Pydantic schema.
# This broke OpenAPI docs, disabled response validation, and meant the frontend
# had no type contract. Added proper response schemas below.

class ResultSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    assignment_id: str
    assignment_title: str
    category: str
    final_score: Optional[float]
    max_score: float
    completed_at: Optional[datetime]


class ResultDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    assignment_id: str
    assignment_title: str
    category: str
    status: str
    final_score: Optional[float]
    max_score: float
    score_breakdown: Optional[dict]
    started_at: datetime
    completed_at: Optional[datetime]
    rejection_reason: Optional[str]
    certificate_available: Optional[bool] = False


@router.get(
    "",
    response_model=list[ResultSummary],
    summary="Get all completed results for the authenticated student",
)
@router.get(
    "/",
    response_model=list[ResultSummary],
    summary="Get all completed results for the authenticated student",
    include_in_schema=False,
)
async def get_my_results(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GradingSession, Assignment)
        .join(Assignment, GradingSession.assignment_id == Assignment.id)
        .where(
            GradingSession.student_id == current_student.id,
            GradingSession.status.in_(COMPLETED_RESULT_STATUSES),
        )
        .order_by(GradingSession.completed_at.desc())
    )
    rows = result.all()
    return [
        ResultSummary(
            id=str(session.id),
            assignment_id=str(assignment.id),
            assignment_title=assignment.title,
            category=assignment.category.value if hasattr(assignment.category, "value") else (assignment.category or "manual_review"),
            final_score=session.final_score,
            max_score=assignment.max_score,
            completed_at=session.completed_at,
        )
        for session, assignment in rows
    ]


@router.get(
    "/{session_id}",
    response_model=ResultDetail,
    summary="Get detailed result for one session",
    responses={404: {"model": ErrorResponse}},
)
async def get_result_detail(
    session_id: str,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    import json
    result = await db.execute(
        select(GradingSession, Assignment)
        .join(Assignment, GradingSession.assignment_id == Assignment.id)
        .where(
            GradingSession.id == uuid.UUID(session_id),
            GradingSession.student_id == current_student.id,
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found",
        )
    session, assignment = row
    breakdown = None
    if session.score_breakdown:
        try:
            breakdown = json.loads(session.score_breakdown)
        except Exception:
            breakdown = None

    return ResultDetail(
        id=str(session.id),
        assignment_id=str(assignment.id),
        assignment_title=assignment.title,
        category=assignment.category or "manual_review",
        status=session.status,
        final_score=session.final_score,
        max_score=assignment.max_score,
        score_breakdown=breakdown,
        started_at=session.started_at,
        completed_at=session.completed_at,
        rejection_reason=session.rejection_reason,
        certificate_available=False,  # TODO: implement certificate check if needed
    )
