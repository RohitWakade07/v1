import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.db.session import get_db
from app.models.models import Mentor, Assignment, GradingSession, Student, SessionStatus
from app.api.v1.dependencies import get_current_mentor
from app.schemas.schemas import (
    AssignmentPublic,
    MentorStudentPublic,
    MentorSessionPublic,
    MentorResultPublic,
    MentorAnalyticsSummary,
)

router = APIRouter(prefix="/mentor", tags=["Mentor Portal Phase 2"])


@router.get(
    "/assignments",
    response_model=List[AssignmentPublic],
    summary="List all assignments for the current mentor",
)
async def list_mentor_assignments(
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assignment)
        .where(Assignment.created_by_id == current_mentor.id)
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
    "/students",
    response_model=List[MentorStudentPublic],
    summary="List students participating in this mentor's assignments",
)
async def list_mentor_students(
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    # Get students who have sessions for this mentor's assignments
    result = await db.execute(
        select(Student, func.count(func.distinct(GradingSession.assignment_id)), func.count(GradingSession.id))
        .join(GradingSession, GradingSession.student_id == Student.id)
        .join(Assignment, GradingSession.assignment_id == Assignment.id)
        .where(Assignment.created_by_id == current_mentor.id)
        .group_by(Student.id)
    )
    
    rows = result.all()
    return [
        MentorStudentPublic(
            id=student.id,
            roll_number=student.roll_number,
            full_name=student.full_name,
            email=student.email,
            assignments_participated=assignments_count,
            sessions_count=sessions_count,
        )
        for student, assignments_count, sessions_count in rows
    ]


@router.get(
    "/sessions",
    response_model=List[MentorSessionPublic],
    summary="List grading sessions for this mentor's assignments",
)
async def list_mentor_sessions(
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GradingSession, Student, Assignment)
        .join(Student, GradingSession.student_id == Student.id)
        .join(Assignment, GradingSession.assignment_id == Assignment.id)
        .where(Assignment.created_by_id == current_mentor.id)
        .order_by(GradingSession.started_at.desc())
    )
    
    rows = result.all()
    return [
        MentorSessionPublic(
            id=session.id,
            student_roll=student.roll_number,
            student_name=student.full_name,
            assignment_slug=assignment.slug,
            assignment_title=assignment.title,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            final_score=session.final_score,
        )
        for session, student, assignment in rows
    ]


@router.get(
    "/results",
    response_model=List[MentorResultPublic],
    summary="List completed results for this mentor's assignments",
)
async def list_mentor_results(
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GradingSession, Student, Assignment)
        .join(Student, GradingSession.student_id == Student.id)
        .join(Assignment, GradingSession.assignment_id == Assignment.id)
        .where(
            Assignment.created_by_id == current_mentor.id,
            GradingSession.status == SessionStatus.COMPLETED,
        )
        .order_by(GradingSession.completed_at.desc())
    )
    
    rows = result.all()
    return [
        MentorResultPublic(
            session_id=session.id,
            student_roll=student.roll_number,
            student_name=student.full_name,
            assignment_slug=assignment.slug,
            assignment_title=assignment.title,
            final_score=session.final_score or 0.0,
            max_score=assignment.max_score,
            completed_at=session.completed_at,
        )
        for session, student, assignment in rows
    ]


@router.get(
    "/analytics/summary",
    response_model=MentorAnalyticsSummary,
    summary="Get analytics summary for mentor dashboard",
)
async def get_mentor_analytics(
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    # Fetch all relevant sessions
    result = await db.execute(
        select(GradingSession, Assignment)
        .join(Assignment, GradingSession.assignment_id == Assignment.id)
        .where(Assignment.created_by_id == current_mentor.id)
    )
    rows = result.all()
    
    total_submissions = len(rows)
    completed_sessions = [r for r in rows if r[0].status == SessionStatus.COMPLETED]
    
    completion_rate = (len(completed_sessions) / total_submissions * 100) if total_submissions > 0 else 0.0
    
    total_score = sum(r[0].final_score or 0.0 for r in completed_sessions)
    avg_score = (total_score / len(completed_sessions)) if completed_sessions else 0.0
    
    # Calculate unique students
    student_ids = set(r[0].student_id for r in rows)
    total_students = len(student_ids)
    
    # Distributions
    score_distribution = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for session, assignment in completed_sessions:
        score_pct = (session.final_score / assignment.max_score * 100) if assignment.max_score > 0 else 0
        if score_pct <= 20: score_distribution["0-20"] += 1
        elif score_pct <= 40: score_distribution["21-40"] += 1
        elif score_pct <= 60: score_distribution["41-60"] += 1
        elif score_pct <= 80: score_distribution["61-80"] += 1
        else: score_distribution["81-100"] += 1
        
    # Assignments participation
    assignments_participation = {}
    for session, assignment in rows:
        assignments_participation[assignment.slug] = assignments_participation.get(assignment.slug, 0) + 1
        
    # Category breakdown
    category_breakdown = {}
    for session, assignment in rows:
        cat = assignment.category.value
        category_breakdown[cat] = category_breakdown.get(cat, 0) + 1

    return MentorAnalyticsSummary(
        total_students=total_students,
        completion_rate=completion_rate,
        avg_score=avg_score,
        total_submissions=total_submissions,
        score_distribution=score_distribution,
        assignments_participation=assignments_participation,
        category_breakdown=category_breakdown,
    )
