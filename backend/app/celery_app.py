import logging
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "grading_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.config_from_object("app.celeryconfig")

import os
if os.environ.get("SERVICE_TYPE") == "worker":
    celery_app.autodiscover_tasks(["workers.tasks"], force=True)
