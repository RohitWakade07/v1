import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.models import Grader, GraderVersion, AssignmentGraderMapping, GraderStatus
from app.repositories.base import BaseRepository

class GraderRepository(BaseRepository[Grader]):
    def __init__(self):
        super().__init__(Grader)

    async def get_active_graders(self, db: AsyncSession) -> List[Grader]:
        result = await db.execute(
            select(Grader)
            .where(Grader.status == GraderStatus.ACTIVE)
            .order_by(Grader.name)
        )
        return result.scalars().all()

class GraderVersionRepository(BaseRepository[GraderVersion]):
    def __init__(self):
        super().__init__(GraderVersion)

    async def get_by_grader(self, db: AsyncSession, *, grader_id: uuid.UUID) -> List[GraderVersion]:
        result = await db.execute(
            select(GraderVersion)
            .where(GraderVersion.grader_id == grader_id)
            .order_by(GraderVersion.created_at.desc())
        )
        return result.scalars().all()

class AssignmentGraderMappingRepository(BaseRepository[AssignmentGraderMapping]):
    def __init__(self):
        super().__init__(AssignmentGraderMapping)

    async def get_by_assignment(self, db: AsyncSession, *, assignment_id: uuid.UUID) -> List[AssignmentGraderMapping]:
        result = await db.execute(
            select(AssignmentGraderMapping)
            .where(AssignmentGraderMapping.assignment_id == assignment_id)
        )
        return result.scalars().all()

    async def get_mapping(self, db: AsyncSession, *, assignment_id: uuid.UUID, grader_id: uuid.UUID) -> Optional[AssignmentGraderMapping]:
        result = await db.execute(
            select(AssignmentGraderMapping)
            .where(AssignmentGraderMapping.assignment_id == assignment_id)
            .where(AssignmentGraderMapping.grader_id == grader_id)
        )
        return result.scalar_one_or_none()

grader_repo = GraderRepository()
grader_version_repo = GraderVersionRepository()
assignment_grader_mapping_repo = AssignmentGraderMappingRepository()
