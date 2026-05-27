from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.session import get_db
from app.models.models import Assignment, Student, Mentor
from app.api.v1.dependencies import get_current_student, get_current_mentor
from app.schemas.schemas import AssignmentPublic, AssignmentCreate, ErrorResponse

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.get(
    "/",
    response_model=list[AssignmentPublic],
    summary="List all published assignments (student view)",
)
async def list_assignments(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all published assignments.
    The grader binary uses this list to show the student which assignment to pick.
    """
    result = await db.execute(
        select(Assignment)
        .where(Assignment.is_published == True)
        .order_by(Assignment.created_at.desc())
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
        )
        for a in assignments
    ]


@router.get(
    "/{assignment_id}",
    response_model=AssignmentPublic,
    responses={404: {"model": ErrorResponse}},
)
async def get_assignment(
    assignment_id: str,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    result = await db.execute(
        select(Assignment).where(
            Assignment.id == uuid.UUID(assignment_id),
            Assignment.is_published == True,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )
    return AssignmentPublic(
        id=assignment.id,
        slug=assignment.slug,
        title=assignment.title,
        description=assignment.description,
        category=assignment.category,
        max_score=assignment.max_score,
        deadline=assignment.deadline,
    )


# ── Mentor-only: create and publish assignments ───────────────────────

@router.post(
    "/",
    response_model=AssignmentPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new assignment (mentor only)",
)
async def create_assignment(
    body: AssignmentCreate,
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Assignment).where(Assignment.slug == body.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Assignment slug '{body.slug}' already exists",
        )
    assignment = Assignment(
        slug=body.slug,
        title=body.title,
        description=body.description,
        category=body.category,
        max_score=body.max_score,
        deadline=body.deadline,
        is_published=False,
        created_by_id=current_mentor.id,
    )
    db.add(assignment)
    await db.flush()
    return AssignmentPublic(
        id=assignment.id,
        slug=assignment.slug,
        title=assignment.title,
        description=assignment.description,
        category=assignment.category,
        max_score=assignment.max_score,
        deadline=assignment.deadline,
    )


@router.post(
    "/{assignment_id}/publish",
    response_model=AssignmentPublic,
    summary="Publish an assignment (mentor only)",
)
async def publish_assignment(
    assignment_id: str,
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    result = await db.execute(
        select(Assignment).where(Assignment.id == uuid.UUID(assignment_id))
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )
    assignment.is_published = True
    db.add(assignment)
    return AssignmentPublic(
        id=assignment.id,
        slug=assignment.slug,
        title=assignment.title,
        description=assignment.description,
        category=assignment.category,
        max_score=assignment.max_score,
        deadline=assignment.deadline,
    )
