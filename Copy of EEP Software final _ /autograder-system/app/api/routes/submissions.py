from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Assignment, Submission, SubmissionStatus, User
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionQueuedResponse,
    SubmissionResponse,
)
from app.tasks.grader import grade_submission

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionQueuedResponse, status_code=status.HTTP_201_CREATED)
def create_submission(payload: SubmissionCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    assignment = db.query(Assignment).filter(Assignment.id == payload.assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    submission = Submission(
        user_id=payload.user_id,
        assignment_id=payload.assignment_id,
        language=payload.language,
        code=payload.code,
        status=SubmissionStatus.pending,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    submission.status = SubmissionStatus.queued
    db.commit()

    grade_submission.delay(submission.id)

    return SubmissionQueuedResponse(
        message="Submission received and queued for grading.",
        submission_id=submission.id,
        status=submission.status.value,
    )

@router.post("/upload", response_model=SubmissionQueuedResponse, status_code=status.HTTP_201_CREATED)
async def upload_submission(
    user_id: int = Form(...),
    assignment_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    content = await file.read()
    try:
        code_text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be a valid UTF-8 text file")

    submission = Submission(
        user_id=user_id,
        assignment_id=assignment_id,
        language="bash",
        code=code_text,
        status=SubmissionStatus.pending,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    submission.status = SubmissionStatus.queued
    db.commit()

    grade_submission.delay(submission.id)

    return SubmissionQueuedResponse(
        message="File uploaded and queued for bash execution.",
        submission_id=submission.id,
        status=submission.status.value if hasattr(submission.status, 'value') else submission.status,
    )



@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    return submission
