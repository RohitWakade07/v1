import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.session import get_db
from app.models.models import Student, Mentor, GradingSession, Assignment, UserRole
from app.api.v1.dependencies import get_current_admin
from app.schemas.schemas import AssignmentPublic
from app.core.security import hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])


# BUG FIX: All admin endpoints were returning raw dicts — no Pydantic schemas,
# no OpenAPI type info, no response validation. Added typed response models
# for all four endpoints below.

class AdminStudentPublic(BaseModel):
    id: str
    roll_number: str
    full_name: str
    email: str
    is_active: bool
    created_at: datetime


class AdminMentorPublic(BaseModel):
    id: str
    username: str
    full_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


class AdminSessionPublic(BaseModel):
    id: str
    student_id: str
    assignment_id: str
    status: str
    started_at: datetime
    submitted_at: Optional[datetime]
    completed_at: Optional[datetime]
    final_score: Optional[float]
    rejection_reason: Optional[str]


# ── Students ──────────────────────────────────────────────────────────

@router.get(
    "/students",
    response_model=list[AdminStudentPublic],
    summary="List all students (admin only)",
)
async def list_all_students(
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Student).order_by(Student.created_at.desc()))
    students = result.scalars().all()
    return [
        AdminStudentPublic(
            id=str(s.id),
            roll_number=s.roll_number,
            full_name=s.full_name,
            email=s.email,
            is_active=s.is_active,
            created_at=s.created_at,
        )
        for s in students
    ]


# ── Mentors ───────────────────────────────────────────────────────────

@router.get(
    "/mentors",
    response_model=list[AdminMentorPublic],
    summary="List all mentors (admin only)",
)
async def list_all_mentors(
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Mentor).order_by(Mentor.created_at.desc()))
    mentors = result.scalars().all()
    return [
        AdminMentorPublic(
            id=str(m.id),
            username=m.username,
            full_name=m.full_name,
            email=m.email,
            role=m.role,
            is_active=m.is_active,
            created_at=m.created_at,
        )
        for m in mentors
    ]


# ── Sessions ──────────────────────────────────────────────────────────

@router.get(
    "/sessions",
    response_model=list[AdminSessionPublic],
    summary="List all grading sessions (admin only)",
)
async def list_all_sessions(
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GradingSession).order_by(GradingSession.started_at.desc())
    )
    sessions = result.scalars().all()
    return [
        AdminSessionPublic(
            id=str(s.id),
            student_id=str(s.student_id),
            assignment_id=str(s.assignment_id),
            status=s.status,
            started_at=s.started_at,
            submitted_at=s.submitted_at,
            completed_at=s.completed_at,
            final_score=s.final_score,
            rejection_reason=s.rejection_reason,
        )
        for s in sessions
    ]


# ── Assignments (all, including unpublished) ──────────────────────────

@router.get(
    "/assignments/all",
    response_model=list[AssignmentPublic],
    summary="List all assignments regardless of status (admin only)",
)
async def list_all_assignments_admin(
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assignment).order_by(Assignment.created_at.desc())
    )
    assignments = result.scalars().all()
    return [
        AssignmentPublic(
            id=a.id,
            slug=a.slug,
            title=a.title,
            description=a.description,
            category=a.category,
            max_score=a.max_score,
            deadline=a.deadline,
            is_published=a.is_published,
            is_archived=a.is_archived,
            created_by_id=a.created_by_id,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in assignments
    ]


# ── Create Mentor (admin only) ────────────────────────────────────────

class CreateMentorRequest(BaseModel):
    username: str
    full_name: str
    email: str
    password: str
    role: str = "mentor"  # "mentor" or "admin"


@router.post(
    "/mentors",
    response_model=AdminMentorPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new mentor or admin account (admin only)",
)
async def create_mentor(
    body: CreateMentorRequest,
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    # Check username uniqueness
    existing = await db.execute(select(Mentor).where(Mentor.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' is already taken.",
        )
    # Check email uniqueness
    existing_email = await db.execute(select(Mentor).where(Mentor.email == body.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{body.email}' is already registered.",
        )

    role = UserRole.ADMIN if body.role == "admin" else UserRole.MENTOR
    mentor = Mentor(
        username=body.username,
        full_name=body.full_name,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=role,
        is_active=True,
    )
    db.add(mentor)
    await db.commit()
    await db.refresh(mentor)

    return AdminMentorPublic(
        id=str(mentor.id),
        username=mentor.username,
        full_name=mentor.full_name,
        email=mentor.email,
        role=mentor.role,
        is_active=mentor.is_active,
        created_at=mentor.created_at,
    )
