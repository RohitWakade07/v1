import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.models import GradingSession, Assignment, SessionStatus, Mentor
from app.schemas.schemas import MentorAnalyticsSummary

class AnalyticsService:
    async def get_mentor_analytics(self, db: AsyncSession, mentor: Mentor) -> MentorAnalyticsSummary:
        result = await db.execute(
            select(GradingSession, Assignment)
            .join(Assignment, GradingSession.assignment_id == Assignment.id)
            .where(Assignment.created_by_id == mentor.id)
        )
        rows = result.all()
        
        total_submissions = len(rows)
        completed_sessions = [r for r in rows if r[0].status in (SessionStatus.VERIFIED, SessionStatus.COMPLETED)]
        
        completion_rate = (len(completed_sessions) / total_submissions * 100) if total_submissions > 0 else 0.0
        
        total_score = sum(r[0].final_score or 0.0 for r in completed_sessions)
        avg_score = (total_score / len(completed_sessions)) if completed_sessions else 0.0
        
        student_ids = set(r[0].student_id for r in rows)
        total_students = len(student_ids)
        
        score_distribution = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
        for session, assignment in completed_sessions:
            score_pct = (session.final_score / assignment.max_score * 100) if assignment.max_score > 0 else 0
            if score_pct <= 20: score_distribution["0-20"] += 1
            elif score_pct <= 40: score_distribution["21-40"] += 1
            elif score_pct <= 60: score_distribution["41-60"] += 1
            elif score_pct <= 80: score_distribution["61-80"] += 1
            else: score_distribution["81-100"] += 1
            
        assignments_participation = {}
        category_breakdown = {}
        for session, assignment in rows:
            assignments_participation[assignment.slug] = assignments_participation.get(assignment.slug, 0) + 1
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

analytics_service = AnalyticsService()
