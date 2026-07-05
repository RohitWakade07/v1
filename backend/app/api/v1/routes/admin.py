import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.session import get_db
from app.models.models import Student, Mentor, Submission, Assignment, UserRole
from app.api.v1.dependencies import get_current_admin
from app.schemas.schemas import AssignmentPublic
from app.core.security import hash_password
from app.schemas.schemas import AssignmentPublic, PaginatedResponse
from sqlalchemy import func
import math

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
    student_name: str
    student_roll: str
    assignment_id: str
    assignment_title: str
    assignment_slug: str
    status: str
    started_at: datetime
    submitted_at: Optional[datetime]
    completed_at: Optional[datetime]
    final_score: Optional[float]
    rejection_reason: Optional[str]


class AdminSubmissionPublic(BaseModel):
    id: str
    student_id: str
    student_name: str
    student_roll: str
    assignment_id: str
    assignment_title: str
    assignment_slug: str
    status: str
    source_type: str
    attempt_number: int
    score: Optional[float]
    max_score: Optional[float]
    passed: Optional[bool]
    submitted_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


# ── Students ──────────────────────────────────────────────────────────

@router.get(
    "/students",
    response_model=PaginatedResponse[AdminStudentPublic],
    summary="List all students with pagination (admin only)",
)
async def list_all_students(
    page: int = 1,
    limit: int = 20,
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    total = await db.execute(select(func.count(Student.id)))
    total_count = total.scalar()
    
    result = await db.execute(
        select(Student)
        .order_by(Student.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    students = result.scalars().all()
    
    data = [
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
    return PaginatedResponse(
        data=data,
        total=total_count,
        page=page,
        pages=math.ceil(total_count / limit) if total_count else 1
    )


# ── Mentors ───────────────────────────────────────────────────────────

@router.get(
    "/mentors",
    response_model=PaginatedResponse[AdminMentorPublic],
    summary="List all mentors with pagination (admin only)",
)
async def list_all_mentors(
    page: int = 1,
    limit: int = 20,
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    total = await db.execute(select(func.count(Mentor.id)))
    total_count = total.scalar()
    
    result = await db.execute(
        select(Mentor)
        .order_by(Mentor.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    mentors = result.scalars().all()
    
    data = [
        AdminMentorPublic(
            id=str(m.id),
            username=m.username,
            full_name=m.full_name,
            email=m.email,
            role=m.role.value if hasattr(m.role, "value") else str(m.role),
            is_active=m.is_active,
            created_at=m.created_at,
        )
        for m in mentors
    ]
    return PaginatedResponse(
        data=data,
        total=total_count,
        page=page,
        pages=math.ceil(total_count / limit) if total_count else 1
    )


# ── Sessions ──────────────────────────────────────────────────────────

@router.get(
    "/sessions",
    response_model=PaginatedResponse[AdminSessionPublic],
    summary="List all grading sessions with pagination (admin only)",
)
async def list_all_sessions(
    page: int = 1,
    limit: int = 20,
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    total = await db.execute(select(func.count(Submission.id)))
    total_count = total.scalar()
    
    result = await db.execute(
        select(Submission, Student, Assignment)
        .join(Student, Submission.student_id == Student.id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .order_by(Submission.started_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = result.all()
    
    data = [
        AdminSessionPublic(
            id=str(s.id),
            student_id=str(s.student_id),
            student_name=student.full_name,
            student_roll=student.roll_number,
            assignment_id=str(s.assignment_id),
            assignment_title=assignment.title,
            assignment_slug=assignment.slug,
            status=s.status.value if hasattr(s.status, "value") else str(s.status),
            started_at=s.started_at or s.submitted_at,
            submitted_at=s.submitted_at,
            completed_at=s.completed_at,
            final_score=s.score,
            rejection_reason=s.validation_error,
        )
        for s, student, assignment in rows
    ]
    return PaginatedResponse(
        data=data,
        total=total_count,
        page=page,
        pages=math.ceil(total_count / limit) if total_count else 1
    )


# ── Submissions (raw queue/processing records) ────────────────────────

@router.get(
    "/submissions",
    response_model=PaginatedResponse[AdminSubmissionPublic],
    summary="List all submissions with pagination (admin only)",
)
async def list_all_submissions_admin(
    page: int = 1,
    limit: int = 20,
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models.models import Submission
    offset = (page - 1) * limit
    total = await db.execute(select(func.count(Submission.id)))
    total_count = total.scalar()
    
    result = await db.execute(
        select(Submission, Student, Assignment)
        .join(Student, Submission.student_id == Student.id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .order_by(Submission.submitted_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = result.all()
    
    data = [
        AdminSubmissionPublic(
            id=str(sub.id),
            student_id=str(sub.student_id),
            student_name=student.full_name,
            student_roll=student.roll_number,
            assignment_id=str(sub.assignment_id),
            assignment_title=assignment.title,
            assignment_slug=assignment.slug,
            status=sub.status.value if hasattr(sub.status, "value") else str(sub.status),
            source_type=sub.source_type.value if hasattr(sub.source_type, "value") else str(sub.source_type),
            attempt_number=sub.attempt_number,
            score=sub.score,
            max_score=sub.max_score,
            passed=sub.passed,
            submitted_at=sub.submitted_at,
            started_at=sub.started_at,
            completed_at=sub.completed_at,
        )
        for sub, student, assignment in rows
    ]
    return PaginatedResponse(
        data=data,
        total=total_count,
        page=page,
        pages=math.ceil(total_count / limit) if total_count else 1
    )


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
        select(Assignment).where(Assignment.is_archived == False).order_by(Assignment.created_at.desc())
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
            late_penalty_pct=a.late_penalty_pct or 0.0,
            submission_filename=a.submission_filename,
            submission_instructions=a.submission_instructions,
              expected_structure=a.expected_structure,
              expected_media_url=a.expected_media_url,
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
        role=mentor.role.value if hasattr(mentor.role, "value") else str(mentor.role),
        is_active=mentor.is_active,
        created_at=mentor.created_at,
    )


# ── Admin Drill-Down Routes ──────────────────────────────────────────

from app.models.models import Classroom, ClassroomEnrollment

@router.get(
    "/mentors/{mentor_id}",
    response_model=AdminMentorPublic,
    summary="Get detailed info for a specific mentor",
)
async def get_mentor_details(
    mentor_id: uuid.UUID,
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Mentor).where(Mentor.id == mentor_id))
    mentor = result.scalar_one_or_none()
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")
    return AdminMentorPublic(
        id=str(mentor.id),
        username=mentor.username,
        full_name=mentor.full_name,
        email=mentor.email,
        role=mentor.role.value if hasattr(mentor.role, "value") else str(mentor.role),
        is_active=mentor.is_active,
        created_at=mentor.created_at,
    )

class AdminClassroomPublic(BaseModel):
    id: str
    name: str
    join_code: str
    created_at: datetime

@router.get(
    "/mentors/{mentor_id}/classrooms",
    response_model=list[AdminClassroomPublic],
    summary="List all classrooms created by a specific mentor",
)
async def list_mentor_classrooms(
    mentor_id: uuid.UUID,
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Classroom).where(Classroom.mentor_id == mentor_id).order_by(Classroom.created_at.desc())
    )
    classrooms = result.scalars().all()
    return [
        AdminClassroomPublic(
            id=str(c.id),
            name=c.name,
            join_code=c.join_code,
            created_at=c.created_at,
        ) for c in classrooms
    ]

@router.get(
    "/classrooms/{classroom_id}",
    response_model=AdminClassroomPublic,
    summary="Get detailed info for a specific classroom",
)
async def get_classroom_details(
    classroom_id: uuid.UUID,
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    return AdminClassroomPublic(
        id=str(classroom.id),
        name=classroom.name,
        join_code=classroom.join_code,
        created_at=classroom.created_at,
    )

@router.get(
    "/classrooms/{classroom_id}/students",
    response_model=PaginatedResponse[AdminStudentPublic],
    summary="List students enrolled in a specific classroom",
)
async def list_classroom_students(
    classroom_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    
    query = (
        select(Student)
        .join(ClassroomEnrollment, ClassroomEnrollment.student_id == Student.id)
        .where(ClassroomEnrollment.classroom_id == classroom_id)
        .where(ClassroomEnrollment.status == "APPROVED")
    )
    
    total = await db.execute(select(func.count()).select_from(query.subquery()))
    total_count = total.scalar()
    
    result = await db.execute(query.order_by(Student.created_at.desc()).offset(offset).limit(limit))
    students = result.scalars().all()
    
    data = [
        AdminStudentPublic(
            id=str(s.id),
            roll_number=s.roll_number,
            full_name=s.full_name,
            email=s.email,
            is_active=s.is_active,
            created_at=s.created_at,
        ) for s in students
    ]
    return PaginatedResponse(
        data=data,
        total=total_count,
        page=page,
        pages=math.ceil(total_count / limit) if total_count else 1
    )

@router.get(
    "/classrooms/{classroom_id}/sessions",
    response_model=PaginatedResponse[AdminSessionPublic],
    summary="List sessions for students in a specific classroom",
)
async def list_classroom_sessions(
    classroom_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    
    base_query = (
        select(Submission, Student, Assignment)
        .join(Student, Submission.student_id == Student.id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .join(ClassroomEnrollment, ClassroomEnrollment.student_id == Student.id)
        .where(ClassroomEnrollment.classroom_id == classroom_id)
        .where(ClassroomEnrollment.status == "APPROVED")
    )
    
    total_query = select(func.count(Submission.id)).join(ClassroomEnrollment, ClassroomEnrollment.student_id == Submission.student_id).where(ClassroomEnrollment.classroom_id == classroom_id).where(ClassroomEnrollment.status == "APPROVED")
    total = await db.execute(total_query)
    total_count = total.scalar()
    
    result = await db.execute(base_query.order_by(Submission.started_at.desc()).offset(offset).limit(limit))
    rows = result.all()
    
    data = [
        AdminSessionPublic(
            id=str(s.id),
            student_id=str(s.student_id),
            student_name=student.full_name,
            student_roll=student.roll_number,
            assignment_id=str(s.assignment_id),
            assignment_title=assignment.title,
            assignment_slug=assignment.slug,
            status=s.status.value if hasattr(s.status, "value") else str(s.status),
            started_at=s.started_at or s.submitted_at,
            submitted_at=s.submitted_at,
            completed_at=s.completed_at,
            final_score=s.score,
            rejection_reason=s.validation_error,
        ) for s, student, assignment in rows
    ]
    return PaginatedResponse(
        data=data,
        total=total_count,
        page=page,
        pages=math.ceil(total_count / limit) if total_count else 1
    )
