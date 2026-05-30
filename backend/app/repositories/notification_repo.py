import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.models import Notification
from app.repositories.base import BaseRepository

class NotificationRepository(BaseRepository[Notification]):
    def __init__(self):
        super().__init__(Notification)

    async def get_by_mentor(self, db: AsyncSession, *, mentor_id: uuid.UUID, unread_only: bool = False) -> List[Notification]:
        query = select(Notification).where(Notification.mentor_id == mentor_id)
        if unread_only:
            query = query.where(Notification.is_read == False)
        query = query.order_by(Notification.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()

notification_repo = NotificationRepository()
