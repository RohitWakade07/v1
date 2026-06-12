import json
import logging
from typing import Any

from confluent_kafka import Producer

from app.core.config import settings

logger = logging.getLogger(__name__)

_producer: Producer | None = None


def get_producer() -> Producer:
    global _producer
    if _producer is None:
        config = settings.kafka_client_config
        config.update({
            "queue.buffering.max.messages": 100000,
            "queue.buffering.max.kbytes": 1048576,
            "batch.num.messages": 1000,
        })
        _producer = Producer(config)
    return _producer


def _delivery_report(err: Exception | None, msg: Any) -> None:
    if err is not None:
        logger.error("Kafka delivery failed for %s: %s", msg.key(), err)
    else:
        logger.debug(
            "Kafka message delivered to %s [%s] at offset %s",
            msg.topic(),
            msg.partition(),
            msg.offset(),
        )


def publish(topic: str, key: str, payload: dict[str, Any]) -> None:
    producer = get_producer()
    message = json.dumps(payload)
    producer.produce(topic, key=key, value=message, callback=_delivery_report)
    producer.poll(0)
    producer.flush()
