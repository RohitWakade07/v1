import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Notification, Mentor
from app.repositories.notification_repo import notification_repo

class NotificationService:
    async def get_notifications(self, db: AsyncSession, mentor: Mentor, unread_only: bool = False) -> List[Notification]:
        return await notification_repo.get_by_mentor(db, mentor_id=mentor.id, unread_only=unread_only)

    async def create_notification(self, db: AsyncSession, mentor_id: uuid.UUID, title: str, message: str) -> Notification:
        notif = Notification(
            mentor_id=mentor_id,
            title=title,
            message=message
        )
        return await notification_repo.create(db, obj_in=notif)

    async def mark_as_read(self, db: AsyncSession, notification_id: uuid.UUID, mentor: Mentor) -> Notification:
        notif = await notification_repo.get(db, id=notification_id)
        if notif and notif.mentor_id == mentor.id:
            return await notification_repo.update(db, db_obj=notif, obj_in={"is_read": True})
        return notif

notification_service = NotificationService()
