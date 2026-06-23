import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.session import get_db
from app.models.models import Assignment, Student, Mentor, UserRole
from app.api.v1.dependencies import get_current_student, get_current_mentor, get_approved_student, get_current_admin
from app.schemas.schemas import AssignmentPublic, AssignmentCreate, AssignmentUpdate, ErrorResponse

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.get(
    "",
    response_model=list[AssignmentPublic],
    summary="List all published assignments (student view)",
)
async def list_assignments(
    current_student: Student = Depends(get_approved_student),
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
            late_penalty_pct=a.late_penalty_pct or 0.0,
            resource_links=a.resource_links,
            submission_filename=a.submission_filename,
            submission_instructions=a.submission_instructions,
            expected_structure=a.expected_structure,
            expected_media_url=a.expected_media_url,
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
    current_student: Student = Depends(get_approved_student),
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
        late_penalty_pct=assignment.late_penalty_pct or 0.0,
        resource_links=assignment.resource_links,
        submission_filename=assignment.submission_filename,
        submission_instructions=assignment.submission_instructions,
          expected_structure=assignment.expected_structure,
          expected_media_url=assignment.expected_media_url,
        created_by_id=assignment.created_by_id,
        created_at=assignment.created_at,
        updated_at=getattr(assignment, "updated_at", None),
    )


@router.post(
    "",
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
        late_penalty_pct=body.late_penalty_pct,
        resource_links=body.resource_links if body.resource_links is not None else [],
        submission_filename=body.submission_filename,
        submission_instructions=body.submission_instructions,
          expected_structure=body.expected_structure,
          expected_media_url=body.expected_media_url,
        is_published=False,
        created_by_id=current_mentor.id,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
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
        late_penalty_pct=assignment.late_penalty_pct or 0.0,
        resource_links=assignment.resource_links,
        submission_filename=assignment.submission_filename,
        submission_instructions=assignment.submission_instructions,
          expected_structure=assignment.expected_structure,
          expected_media_url=assignment.expected_media_url,
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
    await db.commit()
    await db.refresh(assignment)
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
        late_penalty_pct=assignment.late_penalty_pct or 0.0,
        resource_links=assignment.resource_links,
        submission_filename=assignment.submission_filename,
        submission_instructions=assignment.submission_instructions,
          expected_structure=assignment.expected_structure,
          expected_media_url=assignment.expected_media_url,
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
    if current_mentor.role == UserRole.ADMIN:
        result = await db.execute(
            select(Assignment).where(Assignment.id == uuid.UUID(assignment_id))
        )
    else:
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
    await db.commit()
    await db.refresh(assignment)
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
        late_penalty_pct=assignment.late_penalty_pct or 0.0,
        resource_links=assignment.resource_links,
        submission_filename=assignment.submission_filename,
        submission_instructions=assignment.submission_instructions,
          expected_structure=assignment.expected_structure,
          expected_media_url=assignment.expected_media_url,
        created_by_id=assignment.created_by_id,
        created_at=assignment.created_at,
        updated_at=getattr(assignment, "updated_at", None),
    )


@router.patch(
    "/{assignment_id}",
    response_model=AssignmentPublic,
    summary="Update an assignment (owner only, deadline locked after expiry)",
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def update_assignment(
    assignment_id: str,
    body: AssignmentUpdate,
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    if current_mentor.role == UserRole.ADMIN:
        result = await db.execute(
            select(Assignment).where(Assignment.id == _uuid.UUID(assignment_id))
        )
    else:
        result = await db.execute(
            select(Assignment).where(
                Assignment.id == _uuid.UUID(assignment_id),
                Assignment.created_by_id == current_mentor.id,
            )
        )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or not owned by you",
        )

    # Deadline lock: only admin can change deadline after it has passed
    if body.deadline is not None and assignment.deadline and assignment.deadline < datetime.utcnow():
        if current_mentor.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "DEADLINE_LOCKED", "message": "Deadline has already passed. Only an admin can extend it."},
            )

    if body.title is not None:
        assignment.title = body.title
    if body.description is not None:
        assignment.description = body.description
    if body.max_score is not None:
        assignment.max_score = body.max_score
    if body.deadline is not None:
        assignment.deadline = body.deadline

    assignment.updated_at = datetime.utcnow()
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
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
        late_penalty_pct=assignment.late_penalty_pct or 0.0,
        resource_links=assignment.resource_links,
        submission_filename=assignment.submission_filename,
        submission_instructions=assignment.submission_instructions,
          expected_structure=assignment.expected_structure,
          expected_media_url=assignment.expected_media_url,
        created_by_id=assignment.created_by_id,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
    )


# ── Admin: Full assignment CRUD (no ownership restriction) ─────────────

from pydantic import BaseModel
from typing import Optional, List

class AdminAssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    max_score: Optional[float] = None
    deadline: Optional[datetime] = None
    is_published: Optional[bool] = None
    is_archived: Optional[bool] = None
    resource_links: Optional[list] = None
    late_penalty_pct: Optional[float] = None
    submission_filename: Optional[str] = None
    submission_instructions: Optional[str] = None
    expected_structure: Optional[str] = None
    expected_media_url: Optional[str] = None


@router.patch(
    "/admin/{assignment_id}",
    response_model=AssignmentPublic,
    summary="Admin full assignment update — all fields, no deadline lock",
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def admin_update_assignment(
    assignment_id: str,
    body: AdminAssignmentUpdate,
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    assignment = (await db.execute(
        select(Assignment).where(Assignment.id == _uuid.UUID(assignment_id))
    )).scalar_one_or_none()
    if not assignment:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Assignment not found"})

    if body.title is not None: assignment.title = body.title
    if body.description is not None: assignment.description = body.description
    if body.max_score is not None: assignment.max_score = body.max_score
    if body.deadline is not None: assignment.deadline = body.deadline
    if body.is_published is not None: assignment.is_published = body.is_published
    if body.is_archived is not None: assignment.is_archived = body.is_archived
    if body.resource_links is not None: assignment.resource_links = body.resource_links
    if body.late_penalty_pct is not None: assignment.late_penalty_pct = body.late_penalty_pct
    if body.submission_filename is not None: assignment.submission_filename = body.submission_filename
    if body.submission_instructions is not None: assignment.submission_instructions = body.submission_instructions
        if body.expected_structure is not None: assignment.expected_structure = body.expected_structure
        if body.expected_media_url is not None: assignment.expected_media_url = body.expected_media_url
    if body.expected_structure is not None: assignment.expected_structure = body.expected_structure
    if body.expected_media_url is not None: assignment.expected_media_url = body.expected_media_url
    assignment.updated_at = datetime.utcnow()

    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
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
        late_penalty_pct=assignment.late_penalty_pct or 0.0,
        resource_links=assignment.resource_links,
        submission_filename=assignment.submission_filename,
        submission_instructions=assignment.submission_instructions,
          expected_structure=assignment.expected_structure,
          expected_media_url=assignment.expected_media_url,
        created_by_id=assignment.created_by_id,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
    )

@router.delete(
    "/admin/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Admin delete assignment (soft delete by setting is_archived=True)",
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def admin_delete_assignment(
    assignment_id: str,
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    assignment = (await db.execute(
        select(Assignment).where(Assignment.id == _uuid.UUID(assignment_id))
    )).scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Assignment not found"})
        
    assignment.is_archived = True
    await db.commit()
    return None