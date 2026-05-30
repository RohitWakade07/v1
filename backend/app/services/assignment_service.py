import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.models import Assignment, AssignmentConfig, Mentor
from app.repositories.assignment_repo import assignment_repo, assignment_config_repo
from app.schemas.schemas import AssignmentCreate, AssignmentUpdate, AssignmentConfigUpdate

class AssignmentService:
    async def get_assignment(self, db: AsyncSession, assignment_id: uuid.UUID) -> Assignment:
        assignment = await assignment_repo.get(db, id=assignment_id)
        if not assignment or assignment.is_archived:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
        return assignment

    async def get_mentor_assignments(self, db: AsyncSession, mentor_id: uuid.UUID) -> List[Assignment]:
        return await assignment_repo.get_mentor_assignments(db, mentor_id=mentor_id)

    async def create_assignment(self, db: AsyncSession, data: AssignmentCreate, mentor: Mentor) -> Assignment:
        existing = await assignment_repo.get_by_slug(db, slug=data.slug)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Assignment slug already exists")
        
        assignment = Assignment(
            slug=data.slug,
            title=data.title,
            description=data.description,
            category=data.category,
            max_score=data.max_score,
            deadline=data.deadline,
            created_by_id=mentor.id
        )
        return await assignment_repo.create(db, obj_in=assignment)

    async def update_assignment(self, db: AsyncSession, assignment_id: uuid.UUID, data: AssignmentUpdate, mentor: Mentor) -> Assignment:
        assignment = await self.get_assignment(db, assignment_id)
        if assignment.created_by_id != mentor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this assignment")
        
        return await assignment_repo.update(db, db_obj=assignment, obj_in=data)

    async def publish_assignment(self, db: AsyncSession, assignment_id: uuid.UUID, mentor: Mentor) -> Assignment:
        assignment = await self.get_assignment(db, assignment_id)
        if assignment.created_by_id != mentor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
        assignment.is_published = True
        return await assignment_repo.update(db, db_obj=assignment, obj_in={"is_published": True})

    async def unpublish_assignment(self, db: AsyncSession, assignment_id: uuid.UUID, mentor: Mentor) -> Assignment:
        assignment = await self.get_assignment(db, assignment_id)
        if assignment.created_by_id != mentor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
        assignment.is_published = False
        return await assignment_repo.update(db, db_obj=assignment, obj_in={"is_published": False})

    async def get_config(self, db: AsyncSession, assignment_id: uuid.UUID, mentor: Mentor) -> AssignmentConfig:
        assignment = await self.get_assignment(db, assignment_id)
        if assignment.created_by_id != mentor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
        config = await assignment_config_repo.get_by_assignment(db, assignment_id=assignment_id)
        if not config:
            config = AssignmentConfig(assignment_id=assignment_id)
            config = await assignment_config_repo.create(db, obj_in=config)
        return config

    async def update_config(self, db: AsyncSession, assignment_id: uuid.UUID, data: AssignmentConfigUpdate, mentor: Mentor) -> AssignmentConfig:
        config = await self.get_config(db, assignment_id, mentor)
        return await assignment_config_repo.update(db, db_obj=config, obj_in=data)

assignment_service = AssignmentService()
