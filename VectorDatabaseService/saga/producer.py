"""
Producer strana koreografisane SAGA za VectorDatabaseService.

Objavljuje na saga.choreography.exchange:
  - BookCreatedEvent na BOOK_CREATED_KEY        (Korak 2 uspesan -- sve knjige upisane)
  - BookCreationFailedEvent na BOOK_CREATE_FAILED_KEY (Korak 2 neuspesan -- trigeruje kompenzaciju)

Koristi isti aio_pika kanal koji je otvoren u app.py na startup-u (app.state.rabbitmq_channel),
pa nema potrebe za novom konekcijom po pozivu.
"""

import json
import logging

import aio_pika

from config import BOOK_CREATE_FAILED_KEY, BOOK_CREATED_KEY, CHOREOGRAPHY_EXCHANGE
from saga.events import BookCreatedEvent, BookCreationFailedEvent

logger = logging.getLogger(__name__)


async def _publish(channel: aio_pika.abc.AbstractChannel, routing_key: str, payload: dict) -> None:
    exchange = await channel.get_exchange(CHOREOGRAPHY_EXCHANGE)
    message = aio_pika.Message(
        body=json.dumps(payload).encode("utf-8"),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await exchange.publish(message, routing_key=routing_key)


async def publish_book_created(channel: aio_pika.abc.AbstractChannel, event: BookCreatedEvent) -> None:
    payload = event.model_dump(by_alias=True, mode="json")
    await _publish(channel, BOOK_CREATED_KEY, payload)
    logger.info(
        "[CHOREOGRAPHY] sagaId=%s -- BookCreatedEvent objavljen na key=%s",
        event.saga_id, BOOK_CREATED_KEY,
    )


async def publish_book_creation_failed(channel: aio_pika.abc.AbstractChannel, event: BookCreationFailedEvent) -> None:
    payload = event.model_dump(by_alias=True, mode="json")
    await _publish(channel, BOOK_CREATE_FAILED_KEY, payload)
    logger.warning(
        "[CHOREOGRAPHY] sagaId=%s -- BookCreationFailedEvent objavljen na key=%s, razlog=%s",
        event.saga_id, BOOK_CREATE_FAILED_KEY, event.razlog,
    )