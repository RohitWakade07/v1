"""Announcements + Notifications routes."""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete

from app.db.session import get_db
from app.models.models import (
    Announcement, AnnouncementRead, AudienceType,
    Notification, RecipientType, NotificationSourceType,
    Student, Mentor,
)
from app.api.v1.dependencies import (
    get_current_admin, get_current_student, get_current_mentor, get_approved_student,
)

router = APIRouter(tags=["Announcements & Notifications"])

NOTIFICATION_CAP = 5


# ── Schemas ───────────────────────────────────────────────────────────

class AnnouncementCreate(BaseModel):
    title: str
    body: str
    audience: AudienceType = AudienceType.ALL
    expires_at: Optional[datetime] = None


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    audience: Optional[AudienceType] = None
    expires_at: Optional[datetime] = None


class AnnouncementPublic(BaseModel):
    id: uuid.UUID
    admin_id: uuid.UUID
    title: str
    body: str
    audience: AudienceType
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    is_read: bool = False


class NotificationPublic(BaseModel):
    id: uuid.UUID
    recipient_id: uuid.UUID
    recipient_type: RecipientType
    source_type: NotificationSourceType
    source_id: Optional[uuid.UUID]
    title: str
    message: str
    is_read: bool
    created_at: datetime


# ── Helper: fan-out notifications ─────────────────────────────────────

async def _fan_out_announcement(announcement: Announcement, db: AsyncSession):
    """Create notification rows for all eligible recipients, capping at NOTIFICATION_CAP per user."""
    audience = announcement.audience

    async def _push(recipient_id: uuid.UUID, rtype: RecipientType):
        # Enforce cap: delete oldest beyond cap-1
        existing = (await db.execute(
            select(Notification)
            .where(Notification.recipient_id == recipient_id)
            .order_by(Notification.created_at.asc())
        )).scalars().all()

        if len(existing) >= NOTIFICATION_CAP:
            to_delete = existing[:len(existing) - NOTIFICATION_CAP + 1]
            for n in to_delete:
                await db.delete(n)

        notif = Notification(
            recipient_id=recipient_id,
            recipient_type=rtype.value,
            source_type=NotificationSourceType.ANNOUNCEMENT.value,
            source_id=announcement.id,
            title=announcement.title,
            message=announcement.body[:200],
            is_read=False,
        )
        db.add(notif)

    if audience in (AudienceType.STUDENTS, AudienceType.ALL):
        students = (await db.execute(select(Student).where(Student.is_active == True))).scalars().all()
        for s in students:
            await _push(s.id, RecipientType.STUDENT)

    if audience in (AudienceType.MENTORS, AudienceType.ALL):
        mentors = (await db.execute(select(Mentor).where(Mentor.is_active == True))).scalars().all()
        for m in mentors:
            await _push(m.id, RecipientType.MENTOR)

    await db.flush()


# ── Admin: Announcements CRUD ─────────────────────────────────────────

@router.post("/admin/announcements", response_model=AnnouncementPublic, status_code=201, summary="Create announcement (admin)")
async def create_announcement(
    body: AnnouncementCreate,
    admin: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    ann = Announcement(
        admin_id=admin.id,
        title=body.title,
        body=body.body,
        audience=body.audience.value,
        expires_at=body.expires_at,
    )
    db.add(ann)
    await db.flush()
    await _fan_out_announcement(ann, db)
    await db.commit()
    await db.refresh(ann)
    return AnnouncementPublic(**ann.__dict__, is_read=False)


@router.get("/admin/announcements", response_model=List[AnnouncementPublic], summary="List all announcements (admin)")
async def list_announcements_admin(
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    anns = (await db.execute(select(Announcement).order_by(Announcement.created_at.desc()))).scalars().all()
    return [AnnouncementPublic(**a.__dict__, is_read=False) for a in anns]


@router.patch("/admin/announcements/{ann_id}", response_model=AnnouncementPublic, summary="Update announcement (admin)")
async def update_announcement(
    ann_id: str,
    body: AnnouncementUpdate,
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    ann = (await db.execute(select(Announcement).where(Announcement.id == uuid.UUID(ann_id)))).scalar_one_or_none()
    if not ann:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Announcement not found"})
    if body.title is not None: ann.title = body.title
    if body.body is not None: ann.body = body.body
    if body.audience is not None: ann.audience = body.audience.value
    if body.expires_at is not None: ann.expires_at = body.expires_at
    ann.updated_at = datetime.utcnow()
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    return AnnouncementPublic(**ann.__dict__, is_read=False)


@router.delete("/admin/announcements/{ann_id}", status_code=204, summary="Delete announcement (admin)")
async def delete_announcement(
    ann_id: str,
    _: Mentor = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    ann = (await db.execute(select(Announcement).where(Announcement.id == uuid.UUID(ann_id)))).scalar_one_or_none()
    if not ann:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Announcement not found"})
    await db.delete(ann)
    await db.commit()


# ── Student: Announcements ────────────────────────────────────────────

@router.get("/student/announcements", response_model=List[AnnouncementPublic], summary="List announcements for students")
async def list_announcements_student(
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.utcnow()
    anns = (await db.execute(
        select(Announcement)
        .where(
            Announcement.audience.in_([AudienceType.STUDENTS.value, AudienceType.ALL.value]),
            (Announcement.expires_at == None) | (Announcement.expires_at > now),
        )
        .order_by(Announcement.created_at.desc())
    )).scalars().all()

    reads = {
        str(r.announcement_id)
        for r in (await db.execute(
            select(AnnouncementRead).where(AnnouncementRead.user_id == current_student.id)
        )).scalars().all()
    }

    return [AnnouncementPublic(**a.__dict__, is_read=str(a.id) in reads) for a in anns]


@router.post("/student/announcements/{ann_id}/read", status_code=200, summary="Mark announcement as read (student)")
async def mark_announcement_read_student(
    ann_id: str,
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    aid = uuid.UUID(ann_id)
    existing = (await db.execute(
        select(AnnouncementRead).where(AnnouncementRead.announcement_id == aid, AnnouncementRead.user_id == current_student.id)
    )).scalar_one_or_none()
    if not existing:
        db.add(AnnouncementRead(announcement_id=aid, user_id=current_student.id))
        await db.commit()
    return {"message": "Marked as read"}


# ── Mentor: Announcements ─────────────────────────────────────────────

@router.get("/mentor/announcements", response_model=List[AnnouncementPublic], summary="List announcements for mentors")
async def list_announcements_mentor(
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.utcnow()
    anns = (await db.execute(
        select(Announcement)
        .where(
            Announcement.audience.in_([AudienceType.MENTORS.value, AudienceType.ALL.value]),
            (Announcement.expires_at == None) | (Announcement.expires_at > now),
        )
        .order_by(Announcement.created_at.desc())
    )).scalars().all()

    reads = {
        str(r.announcement_id)
        for r in (await db.execute(
            select(AnnouncementRead).where(AnnouncementRead.user_id == current_mentor.id)
        )).scalars().all()
    }

    return [AnnouncementPublic(**a.__dict__, is_read=str(a.id) in reads) for a in anns]


@router.post("/mentor/announcements/{ann_id}/read", status_code=200, summary="Mark announcement as read (mentor)")
async def mark_announcement_read_mentor(
    ann_id: str,
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    aid = uuid.UUID(ann_id)
    existing = (await db.execute(
        select(AnnouncementRead).where(AnnouncementRead.announcement_id == aid, AnnouncementRead.user_id == current_mentor.id)
    )).scalar_one_or_none()
    if not existing:
        db.add(AnnouncementRead(announcement_id=aid, user_id=current_mentor.id))
        await db.commit()
    return {"message": "Marked as read"}


# ── Notifications (unified) ───────────────────────────────────────────

@router.get("/notifications", response_model=List[NotificationPublic], summary="Get top 5 notifications for current user")
async def get_notifications(
    current_student: Optional[Student] = None,
    current_mentor: Optional[Mentor] = None,
    db: AsyncSession = Depends(get_db),
):
    """Returns top 5 notifications. Auth is determined by which token is provided."""
    raise HTTPException(501, detail="Use /student/notifications or /mentor/notifications")


@router.get("/student/notifications", response_model=List[NotificationPublic], summary="Get top 5 notifications for student")
async def get_student_notifications(
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    notifs = (await db.execute(
        select(Notification)
        .where(Notification.recipient_id == current_student.id, Notification.recipient_type == RecipientType.STUDENT.value)
        .order_by(Notification.created_at.desc())
        .limit(NOTIFICATION_CAP)
    )).scalars().all()
    return [NotificationPublic(**n.__dict__) for n in notifs]


@router.post("/student/notifications/{notif_id}/read", status_code=200, summary="Mark notification as read (student)")
async def mark_notification_read_student(
    notif_id: str,
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    nid = uuid.UUID(notif_id)
    notif = (await db.execute(
        select(Notification).where(Notification.id == nid, Notification.recipient_id == current_student.id)
    )).scalar_one_or_none()
    if not notif:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Notification not found"})
    notif.is_read = True
    db.add(notif)
    await db.commit()
    return {"message": "Marked as read"}


@router.post("/student/notifications/read-all", status_code=200, summary="Mark all notifications as read (student)")
async def mark_all_notifications_read_student(
    current_student: Student = Depends(get_approved_student),
    db: AsyncSession = Depends(get_db),
):
    notifs = (await db.execute(
        select(Notification).where(Notification.recipient_id == current_student.id, Notification.is_read == False)
    )).scalars().all()
    for n in notifs:
        n.is_read = True
        db.add(n)
    await db.commit()
    return {"message": f"Marked {len(notifs)} notifications as read"}


@router.get("/mentor/notifications", response_model=List[NotificationPublic], summary="Get top 5 notifications for mentor")
async def get_mentor_notifications(
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    notifs = (await db.execute(
        select(Notification)
        .where(Notification.recipient_id == current_mentor.id, Notification.recipient_type == RecipientType.MENTOR.value)
        .order_by(Notification.created_at.desc())
        .limit(NOTIFICATION_CAP)
    )).scalars().all()
    return [NotificationPublic(**n.__dict__) for n in notifs]


@router.post("/mentor/notifications/{notif_id}/read", status_code=200, summary="Mark notification as read (mentor)")
async def mark_notification_read_mentor(
    notif_id: str,
    current_mentor: Mentor = Depends(get_current_mentor),
    db: AsyncSession = Depends(get_db),
):
    nid = uuid.UUID(notif_id)
    notif = (await db.execute(
        select(Notification).where(Notification.id == nid, Notification.recipient_id == current_mentor.id)
    )).scalar_one_or_none()
    if not notif:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Notification not found"})
    notif.is_read = True
    db.add(notif)
    await db.commit()
    return {"message": "Marked as read"}
