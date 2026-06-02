from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.session import get_db
from app.models.models import Assignment, Student, Mentor
from app.api.v1.dependencies import get_current_student, get_current_mentor
from app.schemas.schemas import AssignmentPublic, AssignmentCreate, AssignmentUpdate, ErrorResponse

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
            is_published=a.is_published,
            is_archived=a.is_archived,
            created_by_id=a.created_by_id,
            created_at=a.created_at,
            updated_at=getattr(a, "updated_at", None),
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
        is_published=assignment.is_published,
        is_archived=assignment.is_archived,
        created_by_id=assignment.created_by_id,
        created_at=assignment.created_at,
        updated_at=getattr(assignment, "updated_at", None),
    )


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
        is_published=assignment.is_published,
        is_archived=assignment.is_archived,
        created_by_id=assignment.created_by_id,
        created_at=assignment.created_at,
        updated_at=getattr(assignment, "updated_at", None),
    )


@router.post(
    "/{assignment_id}/publish",
    response_model=AssignmentPublic,
    summary="Publish an assignment (mentor only, owner only)",
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
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

    # BUG FIX: Previously ANY mentor could publish ANY assignment.
    # Now only the creating mentor (or an admin) may publish it.
    from app.models.models import UserRole
    if assignment.created_by_id != current_mentor.id and current_mentor.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only publish assignments you created",
        )

    assignment.is_published = True
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
        is_published=assignment.is_published,
        is_archived=assignment.is_archived,
        created_by_id=assignment.created_by_id,
        created_at=assignment.created_at,
        updated_at=getattr(assignment, "updated_at", None),
    )


@router.post(
    "/{assignment_id}/unpublish",
    response_model=AssignmentPublic,
    summary="Unpublish an assignment (owner only)",
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def unpublish_assignment(
    assignment_id: str,
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    result = await db.execute(
        select(Assignment).where(
            Assignment.id == uuid.UUID(assignment_id),
            Assignment.created_by_id == current_mentor.id,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or not owned by you",
        )
    assignment.is_published = False
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
        is_published=assignment.is_published,
        is_archived=assignment.is_archived,
        created_by_id=assignment.created_by_id,
        created_at=assignment.created_at,
        updated_at=getattr(assignment, "updated_at", None),
    )


@router.patch(
    "/{assignment_id}",
    response_model=AssignmentPublic,
    summary="Update an assignment (owner only)",
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def update_assignment(
    assignment_id: str,
    body: AssignmentUpdate,
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    result = await db.execute(
        select(Assignment).where(
            Assignment.id == uuid.UUID(assignment_id),
            Assignment.created_by_id == current_mentor.id,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or not owned by you",
        )

    if body.title is not None:
        assignment.title = body.title
    if body.description is not None:
        assignment.description = body.description
    if body.max_score is not None:
        assignment.max_score = body.max_score
    if body.deadline is not None:
        assignment.deadline = body.deadline

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
        is_published=assignment.is_published,
        is_archived=assignment.is_archived,
        created_by_id=assignment.created_by_id,
        created_at=assignment.created_at,
        updated_at=getattr(assignment, "updated_at", None),
    )
