"""Quiz routes — admin management + student attempt."""
import csv
import io
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.session import get_db
from app.models.models import (
    Quiz, QuizQuestion, QuizOption, QuizAttempt, QuizAnswer, QuizAnswerOption,
    QuestionType, Assignment, Student, Submission, SubmissionStatus,
)
from app.api.v1.dependencies import get_current_admin, get_current_student, get_approved_student

router = APIRouter(tags=["Quiz"])


# ── Pydantic Schemas ──────────────────────────────────────────────────

class QuizOptionPublic(BaseModel):
    id: uuid.UUID
    option_text: str
    order_index: int
    is_correct: Optional[bool] = None  # hidden from students


class QuizOptionCreate(BaseModel):
    option_text: str
    is_correct: bool
    order_index: int = 0


class QuizQuestionPublic(BaseModel):
    id: uuid.UUID
    question_text: str
    type: QuestionType
    marks: Optional[int]
    order_index: int
    options: List[QuizOptionPublic] = []


class QuizQuestionCreate(BaseModel):
    question_text: str
    type: QuestionType = QuestionType.SINGLE
    marks: Optional[int] = None
    order_index: int = 0
    options: List[QuizOptionCreate]


class QuizPublic(BaseModel):
    id: uuid.UUID
    assignment_id: uuid.UUID
    title: str
    marks_per_question: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class QuizCreate(BaseModel):
    title: str
    marks_per_question: int = 1
    is_active: bool = False


class QuizUpdate(BaseModel):
    title: Optional[str] = None
    marks_per_question: Optional[int] = None
    is_active: Optional[bool] = None


class QuizAttemptSubmit(BaseModel):
    # Maps question_id -> list of selected option_ids
    answers: dict[str, List[str]]


class QuizAttemptResult(BaseModel):
    attempt_id: uuid.UUID
    quiz_id: uuid.UUID
    total_score: int
    max_score: int
    submitted_at: Optional[datetime]
    question_results: List[dict]


# ── Admin: Quiz CRUD ──────────────────────────────────────────────────

@router.post("/admin/assignments/{assignment_id}/quiz", response_model=QuizPublic, status_code=201, summary="Create quiz for assignment (admin)")
async def create_quiz(
    assignment_id: str,
    body: QuizCreate,
    _: object = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    aid = uuid.UUID(assignment_id)
    # Check assignment exists
    asgn = (await db.execute(select(Assignment).where(Assignment.id == aid))).scalar_one_or_none()
    if not asgn:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Assignment not found"})
    # Check no existing quiz
    existing = (await db.execute(select(Quiz).where(Quiz.assignment_id == aid))).scalar_one_or_none()
    if existing:
        raise HTTPException(409, detail={"error": "QUIZ_EXISTS", "message": "A quiz already exists for this assignment"})

    quiz = Quiz(assignment_id=aid, title=body.title, marks_per_question=body.marks_per_question, is_active=body.is_active)
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
    return QuizPublic(**quiz.__dict__)


@router.get("/admin/assignments/{assignment_id}/quiz", response_model=QuizPublic, summary="Get quiz for assignment (admin)")
async def get_quiz_admin(
    assignment_id: str,
    _: object = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    aid = uuid.UUID(assignment_id)
    quiz = (await db.execute(select(Quiz).where(Quiz.assignment_id == aid))).scalar_one_or_none()
    if not quiz:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "No quiz for this assignment"})
    return QuizPublic(**quiz.__dict__)


@router.patch("/admin/quizzes/{quiz_id}", response_model=QuizPublic, summary="Update quiz settings (admin)")
async def update_quiz(
    quiz_id: str,
    body: QuizUpdate,
    _: object = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    quiz = (await db.execute(select(Quiz).where(Quiz.id == uuid.UUID(quiz_id)))).scalar_one_or_none()
    if not quiz:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Quiz not found"})
    if body.title is not None: quiz.title = body.title
    if body.marks_per_question is not None: quiz.marks_per_question = body.marks_per_question
    if body.is_active is not None: quiz.is_active = body.is_active
    quiz.updated_at = datetime.utcnow()
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
    return QuizPublic(**quiz.__dict__)


# ── Admin: Question Management ────────────────────────────────────────

async def _load_question_with_options(question: QuizQuestion, db: AsyncSession) -> QuizQuestionPublic:
    opts_result = await db.execute(select(QuizOption).where(QuizOption.question_id == question.id).order_by(QuizOption.order_index))
    opts = opts_result.scalars().all()
    return QuizQuestionPublic(
        id=question.id,
        question_text=question.question_text,
        type=question.type,
        marks=question.marks,
        order_index=question.order_index,
        options=[QuizOptionPublic(id=o.id, option_text=o.option_text, order_index=o.order_index, is_correct=o.is_correct) for o in opts],
    )


@router.get("/admin/quizzes/{quiz_id}/questions", response_model=List[QuizQuestionPublic], summary="List quiz questions (admin)")
async def list_questions_admin(
    quiz_id: str,
    _: object = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    qid = uuid.UUID(quiz_id)
    qs = (await db.execute(select(QuizQuestion).where(QuizQuestion.quiz_id == qid).order_by(QuizQuestion.order_index))).scalars().all()
    return [await _load_question_with_options(q, db) for q in qs]


@router.post("/admin/quizzes/{quiz_id}/questions", response_model=QuizQuestionPublic, status_code=201, summary="Add question to quiz (admin)")
async def add_question(
    quiz_id: str,
    body: QuizQuestionCreate,
    _: object = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    qid = uuid.UUID(quiz_id)
    quiz = (await db.execute(select(Quiz).where(Quiz.id == qid))).scalar_one_or_none()
    if not quiz:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Quiz not found"})
    if len(body.options) < 2:
        raise HTTPException(422, detail={"error": "INVALID_OPTIONS", "message": "Each question must have at least 2 options"})
    correct_count = sum(1 for o in body.options if o.is_correct)
    if correct_count == 0:
        raise HTTPException(422, detail={"error": "NO_CORRECT_OPTION", "message": "At least one option must be marked as correct"})
    if body.type == QuestionType.SINGLE and correct_count > 1:
        raise HTTPException(422, detail={"error": "MULTIPLE_CORRECT_FOR_SINGLE", "message": "Single-choice questions must have exactly one correct answer"})

    question = QuizQuestion(quiz_id=qid, question_text=body.question_text, type=body.type.value, marks=body.marks, order_index=body.order_index)
    db.add(question)
    await db.flush()

    for o in body.options:
        opt = QuizOption(question_id=question.id, option_text=o.option_text, is_correct=o.is_correct, order_index=o.order_index)
        db.add(opt)

    await db.commit()
    await db.refresh(question)
    return await _load_question_with_options(question, db)


@router.patch("/admin/questions/{question_id}", response_model=QuizQuestionPublic, summary="Edit question (admin)")
async def edit_question(
    question_id: str,
    body: QuizQuestionCreate,
    _: object = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    qid = uuid.UUID(question_id)
    question = (await db.execute(select(QuizQuestion).where(QuizQuestion.id == qid))).scalar_one_or_none()
    if not question:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Question not found"})
    question.question_text = body.question_text
    question.type = body.type.value
    question.marks = body.marks
    question.order_index = body.order_index

    # Delete old options and recreate
    old_opts = (await db.execute(select(QuizOption).where(QuizOption.question_id == qid))).scalars().all()
    for o in old_opts:
        await db.delete(o)
    await db.flush()
    for o in body.options:
        opt = QuizOption(question_id=question.id, option_text=o.option_text, is_correct=o.is_correct, order_index=o.order_index)
        db.add(opt)
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return await _load_question_with_options(question, db)


@router.delete("/admin/questions/{question_id}", status_code=204, summary="Delete question (admin)")
async def delete_question(
    question_id: str,
    _: object = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    qid = uuid.UUID(question_id)
    question = (await db.execute(select(QuizQuestion).where(QuizQuestion.id == qid))).scalar_one_or_none()
    if not question:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Question not found"})
    await db.delete(question)
    await db.commit()


@router.post("/admin/quizzes/{quiz_id}/questions/csv", response_model=List[QuizQuestionPublic], status_code=201, summary="Bulk import questions via CSV (admin)")
async def import_questions_csv(
    quiz_id: str,
    file: UploadFile = File(...),
    _: object = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """CSV columns: question,option_a,option_b,option_c,option_d,correct_answer,type,marks
    correct_answer: comma-separated letters for multiple (e.g. 'a,c') or single letter for single (e.g. 'b')
    type: 'single' or 'multiple'
    marks: optional integer
    """
    qid = uuid.UUID(quiz_id)
    quiz = (await db.execute(select(Quiz).where(Quiz.id == qid))).scalar_one_or_none()
    if not quiz:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Quiz not found"})

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except Exception:
        raise HTTPException(422, detail={"error": "INVALID_CSV", "message": "File must be UTF-8 encoded CSV"})

    reader = csv.DictReader(io.StringIO(text))
    required = {"question", "option_a", "option_b", "correct_answer", "type"}
    if not required.issubset(set(reader.fieldnames or [])):
        raise HTTPException(422, detail={"error": "INVALID_CSV", "message": f"CSV must have columns: {', '.join(required)} (and optionally option_c, option_d, marks)"})

    created_questions = []
    option_labels = ["a", "b", "c", "d"]

    for i, row in enumerate(reader):
        correct_raw = row.get("correct_answer") or ""
        correct_letters = [c.strip().lower() for c in correct_raw.split(",") if c.strip()]
        
        type_raw = row.get("type") or ""
        q_type = QuestionType.MULTIPLE if type_raw.strip().lower() == "multiple" else QuestionType.SINGLE
        
        marks_raw = row.get("marks") or ""
        marks_val = None
        if marks_raw.strip():
            try:
                marks_val = int(marks_raw.strip())
            except ValueError:
                pass

        question_raw = row.get("question") or ""
        question = QuizQuestion(
            quiz_id=qid,
            question_text=question_raw.strip() or "Untitled Question",
            type=q_type.value,
            marks=marks_val,
            order_index=i,
        )
        db.add(question)
        await db.flush()

        for j, label in enumerate(option_labels):
            col = f"option_{label}"
            val_raw = row.get(col) or ""
            if not val_raw.strip():
                continue
            opt = QuizOption(
                question_id=question.id,
                option_text=val_raw.strip(),
                is_correct=(label in correct_letters),
                order_index=j,
            )
            db.add(opt)

        created_questions.append(question)

    await db.commit()
    results = []
    for q in created_questions:
        await db.refresh(q)
        results.append(await _load_question_with_options(q, db))
    return results


# ── Student: Quiz Access ──────────────────────────────────────────────

@router.get("/student/assignments/{assignment_id}/quiz", response_model=QuizPublic, summary="Get quiz for assignment (student, unlocks after submission)")
async def get_quiz_student(
    assignment_id: str,
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    aid = uuid.UUID(assignment_id)

    # Check student has submitted the assignment
    submission_result = await db.execute(
        select(Submission).where(
            Submission.student_id == current_student.id,
            Submission.assignment_id == aid,
            Submission.status.in_([SubmissionStatus.COMPLETED, SubmissionStatus.FAILED]),
        )
    )
    if not submission_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "QUIZ_LOCKED", "message": "Quiz unlocks only after you submit the weekly task"},
        )

    quiz = (await db.execute(select(Quiz).where(Quiz.assignment_id == aid, Quiz.is_active == True))).scalar_one_or_none()
    if not quiz:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "No active quiz for this assignment"})
    return QuizPublic(**quiz.__dict__)


@router.get("/student/quizzes/{quiz_id}/questions", response_model=List[QuizQuestionPublic], summary="Get quiz questions for student (options hidden is_correct)")
async def get_quiz_questions_student(
    quiz_id: str,
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    qid = uuid.UUID(quiz_id)
    quiz = (await db.execute(select(Quiz).where(Quiz.id == qid, Quiz.is_active == True))).scalar_one_or_none()
    if not quiz:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Quiz not found"})

    # Check if already attempted
    attempt = (await db.execute(select(QuizAttempt).where(QuizAttempt.quiz_id == qid, QuizAttempt.student_id == current_student.id))).scalar_one_or_none()
    if attempt and attempt.submitted_at:
        raise HTTPException(403, detail={"error": "ALREADY_ATTEMPTED", "message": "You have already submitted this quiz"})

    qs = (await db.execute(select(QuizQuestion).where(QuizQuestion.quiz_id == qid).order_by(QuizQuestion.order_index))).scalars().all()
    result = []
    for q in qs:
        opts = (await db.execute(select(QuizOption).where(QuizOption.question_id == q.id).order_by(QuizOption.order_index))).scalars().all()
        result.append(QuizQuestionPublic(
            id=q.id,
            question_text=q.question_text,
            type=q.type,
            marks=q.marks,
            order_index=q.order_index,
            options=[QuizOptionPublic(id=o.id, option_text=o.option_text, order_index=o.order_index) for o in opts],  # is_correct hidden
        ))
    return result


@router.post("/student/quizzes/{quiz_id}/attempt", response_model=QuizAttemptResult, status_code=201, summary="Submit quiz attempt (one per student)")
async def submit_quiz_attempt(
    quiz_id: str,
    body: QuizAttemptSubmit,
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    qid = uuid.UUID(quiz_id)
    quiz = (await db.execute(select(Quiz).where(Quiz.id == qid, Quiz.is_active == True))).scalar_one_or_none()
    if not quiz:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Quiz not found"})

    # Enforce one attempt
    existing = (await db.execute(select(QuizAttempt).where(QuizAttempt.quiz_id == qid, QuizAttempt.student_id == current_student.id))).scalar_one_or_none()
    if existing and existing.submitted_at:
        raise HTTPException(409, detail={"error": "ALREADY_ATTEMPTED", "message": "You have already submitted this quiz"})

    # Create or get attempt
    if not existing:
        attempt = QuizAttempt(quiz_id=qid, student_id=current_student.id)
        db.add(attempt)
        await db.flush()
    else:
        attempt = existing

    # Load all questions and evaluate
    qs = (await db.execute(select(QuizQuestion).where(QuizQuestion.quiz_id == qid))).scalars().all()
    total_score = 0
    max_score = 0
    question_results = []

    for q in qs:
        marks_for_q = q.marks if q.marks is not None else quiz.marks_per_question
        max_score += marks_for_q

        opts = (await db.execute(select(QuizOption).where(QuizOption.question_id == q.id))).scalars().all()
        correct_option_ids = {str(o.id) for o in opts if o.is_correct}
        selected_ids = set(body.answers.get(str(q.id), []))

        is_correct = (selected_ids == correct_option_ids)
        marks_awarded = marks_for_q if is_correct else 0
        total_score += marks_awarded

        answer = QuizAnswer(attempt_id=attempt.id, question_id=q.id, is_correct=is_correct, marks_awarded=marks_awarded)
        db.add(answer)
        await db.flush()

        for opt_id_str in selected_ids:
            try:
                ao = QuizAnswerOption(answer_id=answer.id, option_id=uuid.UUID(opt_id_str))
                db.add(ao)
            except ValueError:
                pass

        question_results.append({
            "question_id": str(q.id),
            "question_text": q.question_text,
            "is_correct": is_correct,
            "marks_awarded": marks_awarded,
            "marks_possible": marks_for_q,
            "correct_option_ids": list(correct_option_ids),
            "selected_option_ids": list(selected_ids),
        })

    attempt.total_score = total_score
    attempt.max_score = max_score
    attempt.submitted_at = datetime.utcnow()
    db.add(attempt)
    await db.commit()

    return QuizAttemptResult(
        attempt_id=attempt.id,
        quiz_id=qid,
        total_score=total_score,
        max_score=max_score,
        submitted_at=attempt.submitted_at,
        question_results=question_results,
    )


@router.get("/student/quizzes/{quiz_id}/result", response_model=QuizAttemptResult, summary="Get quiz result for current student")
async def get_quiz_result_student(
    quiz_id: str,
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    qid = uuid.UUID(quiz_id)
    attempt = (await db.execute(select(QuizAttempt).where(QuizAttempt.quiz_id == qid, QuizAttempt.student_id == current_student.id))).scalar_one_or_none()
    if not attempt or not attempt.submitted_at:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "No completed attempt found for this quiz"})

    answers = (await db.execute(select(QuizAnswer).where(QuizAnswer.attempt_id == attempt.id))).scalars().all()
    question_results = []
    for a in answers:
        q = (await db.execute(select(QuizQuestion).where(QuizQuestion.id == a.question_id))).scalar_one_or_none()
        selected = (await db.execute(select(QuizAnswerOption).where(QuizAnswerOption.answer_id == a.id))).scalars().all()
        question_results.append({
            "question_id": str(a.question_id),
            "question_text": q.question_text if q else "",
            "is_correct": a.is_correct,
            "marks_awarded": a.marks_awarded,
            "selected_option_ids": [str(ao.option_id) for ao in selected],
        })

    return QuizAttemptResult(
        attempt_id=attempt.id,
        quiz_id=qid,
        total_score=attempt.total_score,
        max_score=attempt.max_score,
        submitted_at=attempt.submitted_at,
        question_results=question_results,
    )
