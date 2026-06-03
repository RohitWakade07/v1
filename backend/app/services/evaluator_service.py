import uuid
from typing import List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.models import EvaluatorBuild, Mentor, EvaluatorStatus
from app.repositories.evaluator_repo import evaluator_repo
from app.services.assignment_service import assignment_service

class EvaluatorService:
    async def get_mentor_builds(self, db: AsyncSession, mentor: Mentor) -> List[EvaluatorBuild]:
        return await evaluator_repo.get_by_mentor(db, mentor_id=mentor.id)

    async def get_assignment_builds(self, db: AsyncSession, assignment_id: uuid.UUID, mentor: Mentor) -> List[EvaluatorBuild]:
        # Validate ownership
        await assignment_service.get_assignment(db, assignment_id)
        return await evaluator_repo.get_by_assignment(db, assignment_id=assignment_id)

    async def trigger_build(self, db: AsyncSession, assignment_id: uuid.UUID, mentor: Mentor) -> EvaluatorBuild:
        # Validate ownership
        await assignment_service.get_assignment(db, assignment_id)
        
        build = EvaluatorBuild(
            assignment_id=assignment_id,
            mentor_id=mentor.id,
            status=EvaluatorStatus.SUCCESS, # Stubbed for now
            binary_hash="stubbed_hash_for_now",
            completed_at=datetime.utcnow()
        )
        return await evaluator_repo.create(db, obj_in=build)

evaluator_service = EvaluatorService()
