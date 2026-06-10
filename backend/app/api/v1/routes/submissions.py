import uuid
import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.v1.dependencies import get_approved_student
from app.core.config import settings
from app.db.session import get_db
from app.models.models import Student, Submission, SubmissionSourceType, SubmissionStatus
from app.schemas.schemas import SubmissionCreateResponse, SubmissionPublic, ErrorResponse
from app.services.submission_service import SubmissionService

router = APIRouter(prefix="/submissions", tags=["Submissions"])


@router.post(
    "",
    response_model=SubmissionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
    summary="Create a new assignment submission",
)
async def create_submission(
    assignment_id: uuid.UUID = Form(...),
    source_type: SubmissionSourceType = Form(...),
    repo_url: str | None = Form(None),
    file: UploadFile | None = File(None),
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    if source_type == SubmissionSourceType.ZIP and not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ZIP file is required for zip submissions",
        )

    zip_bytes = None
    if file:
        if file.content_type != "application/zip":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only ZIP archives are accepted for uploads",
            )
        zip_bytes = await file.read()
        if len(zip_bytes) > settings.EEP_MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Uploaded ZIP exceeds maximum size of {settings.EEP_MAX_UPLOAD_BYTES} bytes",
            )

    return await SubmissionService.submit_assignment(
        student=current_student,
        assignment_id=assignment_id,
        source_type=source_type,
        repo_url=repo_url,
        zip_bytes=zip_bytes,
        db=db,
    )


@router.get(
    "",
    response_model=list[SubmissionPublic],
    summary="List all submissions of the authenticated student",
)
async def list_submissions(
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Submission)
        .where(Submission.student_id == current_student.id)
        .order_by(Submission.submitted_at.desc())
    )
    return result.scalars().all()


@router.get(
    "/{submission_id}",
    response_model=SubmissionPublic,
    summary="Get details of a specific submission",
    responses={404: {"model": ErrorResponse}},
)
async def get_submission_detail(
    submission_id: uuid.UUID,
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Submission).where(
            Submission.id == submission_id,
            Submission.student_id == current_student.id,
        )
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )
    return submission


@router.post(
    "/{submission_id}/cancel",
    response_model=SubmissionPublic,
    summary="Cancel a pending or queued submission",
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def cancel_submission(
    submission_id: uuid.UUID,
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Submission).where(
            Submission.id == submission_id,
            Submission.student_id == current_student.id,
        )
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )
    if submission.status not in (SubmissionStatus.PENDING, SubmissionStatus.QUEUED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending or queued submissions can be cancelled",
        )
    submission.status = SubmissionStatus.CANCELLED
    submission.completed_at = datetime.utcnow()
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


@router.get(
    "/{submission_id}/status",
    summary="Stream submission status updates via Server-Sent Events (SSE)",
)
async def stream_submission_status(
    submission_id: uuid.UUID,
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Submission).where(
            Submission.id == submission_id,
            Submission.student_id == current_student.id,
        )
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    async def event_generator():
        last_status = None
        while True:
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                res = await session.execute(
                    select(Submission).where(Submission.id == submission_id)
                )
                sub = res.scalar_one_or_none()
                if not sub:
                    yield "event: error\ndata: Submission deleted\n\n"
                    break

                if sub.status != last_status:
                    last_status = sub.status
                    yield f"event: status\ndata: {sub.status.value}\n\n"

                if sub.status in (
                    SubmissionStatus.COMPLETED,
                    SubmissionStatus.FAILED,
                    SubmissionStatus.TIMEOUT,
                    SubmissionStatus.CANCELLED,
                    SubmissionStatus.VALIDATION_ERROR,
                ):
                    break

            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
