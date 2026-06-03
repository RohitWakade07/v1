import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from sqlmodel import select
from app.db.session import get_db
from app.api.v1.dependencies import get_current_student
from app.models.models import Student, ClassroomEnrollment, Classroom, Mentor
from app.schemas.schemas import StudentProfileResponse

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/me", response_model=StudentProfileResponse)
async def get_my_profile(
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

    classroom_name = None
    classroom_status = None
    mentor_name = None
    if row:
        enrollment, classroom, mentor = row
        classroom_name = classroom.name
        classroom_status = enrollment.status
        mentor_name = mentor.full_name

    return StudentProfileResponse(
        full_name=current_student.full_name,
        email=current_student.email,
        roll_number=current_student.roll_number,
        student_uuid=current_student.id,
        classroom_name=classroom_name,
        classroom_status=classroom_status,
        mentor_name=mentor_name,
    )
