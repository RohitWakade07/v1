from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

_sync_engine = create_engine(settings.DATABASE_URL_SYNC, future=True)
SyncSessionLocal = sessionmaker(bind=_sync_engine, expire_on_commit=False, class_=Session)
