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
    while True:
        try:
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
