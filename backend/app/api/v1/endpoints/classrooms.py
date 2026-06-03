import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.session import get_db
from app.models.models import Classroom, ClassroomEnrollment, Student, Mentor
from app.api.v1.dependencies import get_current_student, get_current_mentor
from app.schemas.schemas import (
    ClassroomCreate,
    ClassroomPublic,
    ClassroomJoinRequest,
    ClassroomStudentEnrollmentResponse,
)

router = APIRouter(prefix="/classrooms", tags=["Classrooms"])


# ── Mentor Endpoints ──────────────────────────────────────────────────

@router.post(
    "",
    response_model=ClassroomPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new classroom (mentor only)",
)
async def create_classroom(
    body: ClassroomCreate,
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    name_stripped = body.name.strip()
    if not name_stripped:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Classroom name cannot be empty",
        )

    # Generate a unique 6-character uppercase alphanumeric class code
    attempts = 0
    class_code = ""
    while attempts < 10:
        candidate = f"CLASS-{uuid.uuid4().hex[:6].upper()}"
        existing_result = await db.execute(
            select(Classroom).where(Classroom.class_code == candidate)
        )
        if not existing_result.scalar_one_or_none():
            class_code = candidate
            break
        attempts += 1

    if not class_code:
        class_code = f"CLASS-{uuid.uuid4().hex[:8].upper()}"

    classroom = Classroom(
        name=name_stripped,
        class_code=class_code,
        mentor_id=current_mentor.id,
    )
    db.add(classroom)
    await db.flush()

    return ClassroomPublic(
        id=classroom.id,
        name=classroom.name,
        class_code=classroom.class_code,
        mentor_id=classroom.mentor_id,
        created_at=classroom.created_at,
    )


@router.get(
    "",
    response_model=List[ClassroomPublic],
    summary="List classrooms created by the current mentor",
)
async def list_mentor_classrooms(
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Classroom)
        .where(Classroom.mentor_id == current_mentor.id)
        .order_by(Classroom.created_at.desc())
    )
    classrooms = result.scalars().all()
    return [
        ClassroomPublic(
            id=c.id,
            name=c.name,
            class_code=c.class_code,
            mentor_id=c.mentor_id,
            created_at=c.created_at,
        )
        for c in classrooms
    ]


@router.get(
    "/{classroom_id}/enrollments",
    response_model=List[ClassroomStudentEnrollmentResponse],
    summary="List student enrollments for a classroom (mentor only)",
)
async def list_classroom_enrollments(
    classroom_id: str,
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    cls_uuid = uuid.UUID(classroom_id)
    # Verify mentor owns this classroom
    classroom_result = await db.execute(
        select(Classroom).where(
            Classroom.id == cls_uuid,
            Classroom.mentor_id == current_mentor.id,
        )
    )
    if not classroom_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found or not owned by you",
        )

    result = await db.execute(
        select(ClassroomEnrollment, Student)
        .join(Student, ClassroomEnrollment.student_id == Student.id)
        .where(ClassroomEnrollment.classroom_id == cls_uuid)
        .order_by(ClassroomEnrollment.joined_at.desc())
    )
    rows = result.all()

    return [
        ClassroomStudentEnrollmentResponse(
            enrollment_id=enrollment.id,
            student_id=student.id,
            student_name=student.full_name,
            student_roll=student.roll_number,
            student_email=student.email,
            status=enrollment.status,
            joined_at=enrollment.joined_at,
        )
        for enrollment, student in rows
    ]


@router.post(
    "/enrollments/{enrollment_id}/approve",
    summary="Approve a student's classroom enrollment request (mentor only)",
)
async def approve_enrollment(
    enrollment_id: str,
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    enroll_uuid = uuid.UUID(enrollment_id)
    result = await db.execute(
        select(ClassroomEnrollment, Classroom)
        .join(Classroom, ClassroomEnrollment.classroom_id == Classroom.id)
        .where(ClassroomEnrollment.id == enroll_uuid)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment request not found",
        )

    enrollment, classroom = row
    if classroom.mentor_id != current_mentor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to approve enrollments for this classroom",
        )

    enrollment.status = "APPROVED"
    db.add(enrollment)
    await db.flush()
    return {"message": "Student enrollment approved successfully"}


@router.post(
    "/enrollments/{enrollment_id}/reject",
    summary="Reject a student's classroom enrollment request (mentor only)",
)
async def reject_enrollment(
    enrollment_id: str,
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    enroll_uuid = uuid.UUID(enrollment_id)
    result = await db.execute(
        select(ClassroomEnrollment, Classroom)
        .join(Classroom, ClassroomEnrollment.classroom_id == Classroom.id)
        .where(ClassroomEnrollment.id == enroll_uuid)
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment request not found",
        )

    enrollment, classroom = row
    if classroom.mentor_id != current_mentor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to reject enrollments for this classroom",
        )

    enrollment.status = "REJECTED"
    db.add(enrollment)
    await db.flush()
    return {"message": "Student enrollment rejected successfully"}


# ── Student Endpoints ─────────────────────────────────────────────────

@router.post(
    "/join",
    summary="Join a classroom using a class code (student only)",
)
async def join_classroom(
    body: ClassroomJoinRequest,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    code_clean = body.class_code.strip().upper()
    if not code_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class code cannot be empty",
        )

    # Find classroom by class_code
    classroom_result = await db.execute(
        select(Classroom).where(Classroom.class_code == code_clean)
    )
    classroom = classroom_result.scalar_one_or_none()
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid class code — please check with your mentor.",
        )

    # Check if student already has a pending or approved enrollment
    existing_result = await db.execute(
        select(ClassroomEnrollment).where(
            ClassroomEnrollment.student_id == current_student.id
        )
    )
    existing_enrollments = existing_result.scalars().all()

    for e in existing_enrollments:
        if e.status == "APPROVED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You are already approved in classroom '{classroom.name}' and cannot join a new one.",
            )
        # Clear out any stale pending/rejected enrollment requests
        await db.delete(e)

    # Create new PENDING enrollment
    enrollment = ClassroomEnrollment(
        classroom_id=classroom.id,
        student_id=current_student.id,
        status="PENDING",
    )
    db.add(enrollment)
    await db.flush()

    return {
        "message": f"Successfully requested to join classroom '{classroom.name}'. Pending mentor approval.",
        "classroom_name": classroom.name,
    }


@router.get(
    "/my-status",
    summary="Check current student enrollment status",
)
async def get_my_enrollment_status(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClassroomEnrollment, Classroom, Mentor)
        .join(Classroom, ClassroomEnrollment.classroom_id == Classroom.id)
        .join(Mentor, Classroom.mentor_id == Mentor.id)
        .where(ClassroomEnrollment.student_id == current_student.id)
    )
    row = result.first()

    if not row:
        return {
            "classroom_name": None,
            "classroom_status": None,
            "mentor_name": None,
        }

    enrollment, classroom, mentor = row
    return {
        "classroom_name": classroom.name,
        "classroom_status": enrollment.status,
        "mentor_name": mentor.full_name,
    }
