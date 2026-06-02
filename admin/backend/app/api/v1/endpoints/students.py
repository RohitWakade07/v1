import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.dependencies import get_current_student
from app.models.models import Student
from app.schemas.schemas import StudentProfileResponse

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/me", response_model=StudentProfileResponse)
async def get_my_profile(
    current_student: Student = Depends(get_current_student),
):
    return StudentProfileResponse(
        full_name=current_student.full_name,
        email=current_student.email,
        roll_number=current_student.roll_number,
        student_uuid=current_student.id,
    )
