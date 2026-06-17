import asyncio
import json
import logging
from datetime import datetime

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.models import SubmissionOutbox
from app.celery_app import celery_app

logger = logging.getLogger(__name__)

async def poll_outbox():
    logger.info("Starting Celery outbox poller...")
    import redis.asyncio as aioredis
    from app.core.config import settings
    redis_client = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    lock_key = "celery_outbox_poller_lock"

    while True:
        try:
            # Attempt to acquire a short-lived lock
            lock_acquired = await redis_client.set(lock_key, "locked", nx=True, ex=10)
            if not lock_acquired:
                # Another worker is polling, sleep and try again later
                await asyncio.sleep(5)
                continue

            async with AsyncSessionLocal() as db:
                # Fetch undispatched
                result = await db.execute(
                    select(SubmissionOutbox)
                    .where(SubmissionOutbox.dispatched_at == None)
                    .order_by(SubmissionOutbox.created_at)
                    .limit(50)
                )
                records = result.scalars().all()

                if not records:
                    await asyncio.sleep(2)
                    continue

                for record in records:
                    try:
                        payload = json.loads(record.payload)
                        # Send to Celery broker
                        celery_app.send_task(
                            "workers.tasks.grade_submission_task",
                            kwargs={"submission_id": payload["submission_id"]},
                            queue="normal"
                        )
                        record.dispatched_at = datetime.utcnow()
                    except Exception as e:
                        logger.error(f"Failed to dispatch record {record.id}: {e}")
                        record.retry_count += 1
                
                await db.commit()
        except Exception as e:
            logger.error(f"Outbox poller DB error: {e}")
            await asyncio.sleep(5)
