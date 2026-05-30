import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.models import Grader, GraderVersion, AssignmentGraderMapping, Mentor
from app.repositories.grader_repo import grader_repo, grader_version_repo, assignment_grader_mapping_repo
from app.services.assignment_service import assignment_service

class GraderService:
    async def get_active_graders(self, db: AsyncSession) -> List[Grader]:
        return await grader_repo.get_active_graders(db)

    async def get_grader_versions(self, db: AsyncSession, grader_id: uuid.UUID) -> List[GraderVersion]:
        grader = await grader_repo.get(db, id=grader_id)
        if not grader:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grader not found")
        return await grader_version_repo.get_by_grader(db, grader_id=grader_id)

    async def link_grader_to_assignment(
        self, db: AsyncSession, assignment_id: uuid.UUID, grader_id: uuid.UUID, version_id: uuid.UUID, mentor: Mentor
    ) -> AssignmentGraderMapping:
        # Validate assignment ownership
        await assignment_service.get_assignment(db, assignment_id)
        
        # Verify grader and version exist
        version = await grader_version_repo.get(db, id=version_id)
        if not version or version.grader_id != grader_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid grader version")

        # Check existing mapping
        existing = await assignment_grader_mapping_repo.get_mapping(db, assignment_id=assignment_id, grader_id=grader_id)
        if existing:
            return await assignment_grader_mapping_repo.update(db, db_obj=existing, obj_in={"grader_version_id": version_id})
        
        mapping = AssignmentGraderMapping(
            assignment_id=assignment_id,
            grader_id=grader_id,
            grader_version_id=version_id
        )
        return await assignment_grader_mapping_repo.create(db, obj_in=mapping)

grader_service = GraderService()
