import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.models import Assignment, AssignmentConfig
from app.repositories.base import BaseRepository

class AssignmentRepository(BaseRepository[Assignment]):
    def __init__(self):
        super().__init__(Assignment)

    async def get_by_slug(self, db: AsyncSession, *, slug: str) -> Optional[Assignment]:
        result = await db.execute(select(Assignment).where(Assignment.slug == slug))
        return result.scalar_one_or_none()

    async def get_mentor_assignments(self, db: AsyncSession, *, mentor_id: uuid.UUID) -> List[Assignment]:
        result = await db.execute(
            select(Assignment)
            .where(Assignment.created_by_id == mentor_id)
            .where(Assignment.is_archived == False)
            .order_by(Assignment.created_at.desc())
        )
        return result.scalars().all()

    async def get_published_assignments(self, db: AsyncSession) -> List[Assignment]:
        result = await db.execute(
            select(Assignment)
            .where(Assignment.is_published == True)
            .where(Assignment.is_archived == False)
            .order_by(Assignment.created_at.desc())
        )
        return result.scalars().all()

class AssignmentConfigRepository(BaseRepository[AssignmentConfig]):
    def __init__(self):
        super().__init__(AssignmentConfig)

    async def get_by_assignment(self, db: AsyncSession, *, assignment_id: uuid.UUID) -> Optional[AssignmentConfig]:
        result = await db.execute(select(AssignmentConfig).where(AssignmentConfig.assignment_id == assignment_id))
        return result.scalar_one_or_none()

assignment_repo = AssignmentRepository()
assignment_config_repo = AssignmentConfigRepository()
