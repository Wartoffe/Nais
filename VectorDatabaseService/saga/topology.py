"""
Deklarise istu RabbitMQ topologiju koju vec deklarise RabbitMQConfig.java na strani
TimeseriesDatabaseService (exchange tipa "topic", 4 durable queue-a, 4 binding-a).

RabbitMQ declare operacije su idempotentne SAMO ako su parametri identicni svakom
servisu koji ih deklarise -- otud topic/durable vrednosti ovde MORAJU odgovarati
Java strani, ili ce AMQP konekcija pucati sa 406 PRECONDITION_FAILED.

Pozivamo ovo na startup VectorDatabaseService-a kako bismo bili sigurni da
topologija postoji nezavisno od redosleda paljenja servisa (ko prvi krene,
taj je i deklarise).
"""

import logging

import aio_pika

from config import (
    BOOK_CREATE_FAILED_KEY,
    BOOK_CREATE_FAILED_QUEUE,
    BOOK_CREATED_KEY,
    BOOK_CREATED_QUEUE,
    CHOREOGRAPHY_EXCHANGE,
    ORDERSTATUS_COMPENSATED_KEY,
    ORDERSTATUS_COMPENSATED_QUEUE,
    ORDERSTATUS_CREATED_KEY,
    ORDERSTATUS_CREATED_QUEUE,
)

logger = logging.getLogger(__name__)


async def declare_choreography_topology(channel: aio_pika.abc.AbstractChannel) -> None:
    exchange = await channel.declare_exchange(
        CHOREOGRAPHY_EXCHANGE,
        aio_pika.ExchangeType.TOPIC,
        durable=True,
    )

    orderstatus_created_queue = await channel.declare_queue(ORDERSTATUS_CREATED_QUEUE, durable=True)
    book_created_queue = await channel.declare_queue(BOOK_CREATED_QUEUE, durable=True)
    book_create_failed_queue = await channel.declare_queue(BOOK_CREATE_FAILED_QUEUE, durable=True)
    orderstatus_compensated_queue = await channel.declare_queue(ORDERSTATUS_COMPENSATED_QUEUE, durable=True)

    await orderstatus_created_queue.bind(exchange, routing_key=ORDERSTATUS_CREATED_KEY)
    await book_created_queue.bind(exchange, routing_key=BOOK_CREATED_KEY)
    await book_create_failed_queue.bind(exchange, routing_key=BOOK_CREATE_FAILED_KEY)
    await orderstatus_compensated_queue.bind(exchange, routing_key=ORDERSTATUS_COMPENSATED_KEY)

    logger.info("[CHOREOGRAPHY] RabbitMQ topologija deklarisana (exchange=%s)", CHOREOGRAPHY_EXCHANGE)