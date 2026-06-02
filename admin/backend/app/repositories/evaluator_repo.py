import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.models import EvaluatorBuild
from app.repositories.base import BaseRepository

class EvaluatorBuildRepository(BaseRepository[EvaluatorBuild]):
    def __init__(self):
        super().__init__(EvaluatorBuild)

    async def get_by_assignment(self, db: AsyncSession, *, assignment_id: uuid.UUID) -> List[EvaluatorBuild]:
        result = await db.execute(
            select(EvaluatorBuild)
            .where(EvaluatorBuild.assignment_id == assignment_id)
            .order_by(EvaluatorBuild.started_at.desc())
        )
        return result.scalars().all()

    async def get_by_mentor(self, db: AsyncSession, *, mentor_id: uuid.UUID) -> List[EvaluatorBuild]:
        result = await db.execute(
            select(EvaluatorBuild)
            .where(EvaluatorBuild.mentor_id == mentor_id)
            .order_by(EvaluatorBuild.started_at.desc())
        )
        return result.scalars().all()

evaluator_repo = EvaluatorBuildRepository()
