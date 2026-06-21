"""
Korak 2 koreografisane SAGA (VectorDatabaseService strana).

Slusa ORDERSTATUS_CREATED_QUEUE. Po prijemu ChangeOfOrderStatusCreatedEvent-a:
  1. Za svaku knjigu iz event.knjige radi insert u Milvus (description_embedding
     i cover_embedding se generisu unutar books_service.batch_create_books).
  2. Ako insert za SVE knjige uspe -> objavljuje BookCreatedEvent na BOOK_CREATED_KEY.
  3. Ako insert ne uspe (ili je lista knjiga prazna/nevalidna) -> objavljuje
     BookCreationFailedEvent na BOOK_CREATE_FAILED_KEY, prosledjujuci prethodniStatus
     nepromenjen kako bi CompensationListener (TimeseriesDatabaseService) znao na sta
     da vrati narudzbinu.

Idempotentnost:
  Milvus auto-generise primarni kljuc (id) i NEMA unique constraint na goodreads_id,
  pa bismo kod redelivery-a (npr. RabbitMQ requeue nakon pada konekcije) mogli upisati
  istu knjigu dva puta. Zbog toga se PRE insert-a provera da li knjiga sa istim
  goodreads_id vec postoji (preko books_repository.find_all sa filterom) -- ako da,
  taj zapis se preskace (ne tretira se kao greska), u skladu sa komentarom u
  LibraryInfluxController.java ("U slucaju da knjiga vec postoji u bazi, samo ce se
  preskociti i nastaviti dalje sa ostalima").
"""

import logging

import aio_pika

from config import ORDERSTATUS_CREATED_QUEUE
from model.book import BookCreate
from repository.books_repository import books_repository
from saga.events import BookCreatedEvent, BookCreationFailedEvent, ChangeOfOrderStatusCreatedEvent
from saga.producer import publish_book_created, publish_book_creation_failed
from service.impl.books_service import books_service

logger = logging.getLogger(__name__)


def _sanitize_goodreads_id(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _book_already_exists(goodreads_id: int) -> bool:
    """Provera da li knjiga sa datim goodreads_id vec postoji u kolekciji (idempotentnost)."""
    filter_expr = f'goodreads_id == "{_sanitize_goodreads_id(str(goodreads_id))}"'
    existing = books_repository.find_all(filter_expr, limit=1, offset=0)
    return len(existing) > 0


async def _handle_order_status_created(
    channel: aio_pika.abc.AbstractChannel,
    event: ChangeOfOrderStatusCreatedEvent,
) -> None:
    saga_id = event.saga_id
    logger.info(
        "[CHOREOGRAPHY] sagaId=%s -- primljen ChangeOfOrderStatusCreatedEvent za narudzbinaid=%s, broj knjiga=%d",
        saga_id, event.narudzbinaid, len(event.knjige),
    )

    if not event.knjige:
        await _fail(channel, event, "Lista knjiga je prazna -- nema sta da se unese u Milvus.")
        return

    books_to_insert: list[BookCreate] = []
    skipped_goodreads_ids: list[int] = []

    try:
        for knjiga in event.knjige:
            if _book_already_exists(knjiga.goodreads_id):
                skipped_goodreads_ids.append(knjiga.goodreads_id)
                continue
            books_to_insert.append(
                BookCreate(
                    goodreads_id=knjiga.goodreads_id,
                    isbn=knjiga.isbn,
                    title=knjiga.title,
                    author=knjiga.author,
                    description=knjiga.description,
                    language=knjiga.language,
                    publisher=knjiga.publisher,
                    pages=knjiga.pages,
                    coverImg=knjiga.cover_img,
                    has_image=knjiga.has_image,
                )
            )

        if skipped_goodreads_ids:
            logger.info(
                "[CHOREOGRAPHY] sagaId=%s -- preskocene vec postojece knjige, goodreads_id=%s",
                saga_id, skipped_goodreads_ids,
            )

        if books_to_insert:
            result = books_service.batch_create_books(books_to_insert)
            logger.info(
                "[CHOREOGRAPHY] sagaId=%s -- uspesan insert %d/%d knjiga u Milvus (insert_count=%s)",
                saga_id, len(books_to_insert), len(event.knjige), result.get("insert_count"),
            )
        else:
            logger.info(
                "[CHOREOGRAPHY] sagaId=%s -- sve knjige iz eventa su vec postojale, nema sta da se insert-uje",
                saga_id,
            )

    except Exception as exc:  # noqa: BLE001 -- bilo koji pad insert-a mora trigerovati kompenzaciju
        logger.error("[CHOREOGRAPHY] sagaId=%s -- GRESKA prilikom insert-a u Milvus: %s", saga_id, exc, exc_info=True)
        await _fail(channel, event, f"Insert u Milvus nije uspeo: {exc}")
        return

    created_event = BookCreatedEvent(sagaId=saga_id, narudzbinaid=event.narudzbinaid, timestamp=event.timestamp)
    try:
        await publish_book_created(channel, created_event)
    except Exception as exc:  # noqa: BLE001
        # Insert je prosao, ali objava uspeha nije -- nema rollback-a unazad (knjige ostaju
        # u Milvusu), samo logujemo. SagaCompletionListener nece primiti potvrdu, pa ce SAGA
        # ostati "open" sa stanovista Timeseries strane -- ovo je poznato ogranicenje
        # choreography pristupa bez transakcionog outbox-a.
        logger.error(
            "[CHOREOGRAPHY] sagaId=%s -- insert OK, ali objava BookCreatedEvent NIJE uspela: %s",
            saga_id, exc, exc_info=True,
        )


async def _fail(
    channel: aio_pika.abc.AbstractChannel,
    event: ChangeOfOrderStatusCreatedEvent,
    razlog: str,
) -> None:
    failed_event = BookCreationFailedEvent(
        sagaId=event.saga_id,
        narudzbinaid=event.narudzbinaid,
        prethodniStatus=event.prethodni_status,
        razlog=razlog,
        timestamp=event.timestamp,
    )
    try:
        await publish_book_creation_failed(channel, failed_event)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "[CHOREOGRAPHY] sagaId=%s -- KRITICNO: insert nije uspeo I objava BookCreationFailedEvent nije uspela: %s. "
            "Kompenzacija na Timeseries strani se NECE pokrenuti za narudzbinaid=%s.",
            event.saga_id, exc, event.narudzbinaid, exc_info=True,
        )


async def on_message(channel: aio_pika.abc.AbstractChannel, message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        try:
            event = ChangeOfOrderStatusCreatedEvent.model_validate_json(message.body)
        except Exception as exc:  # noqa: BLE001
            logger.error("[CHOREOGRAPHY] Neuspesno parsiranje ChangeOfOrderStatusCreatedEvent: %s", exc, exc_info=True)
            return

        await _handle_order_status_created(channel, event)


async def start_orderstatus_created_consumer(channel: aio_pika.abc.AbstractChannel) -> None:
    queue = await channel.get_queue(ORDERSTATUS_CREATED_QUEUE)
    await queue.consume(lambda message: on_message(channel, message))
    logger.info("[CHOREOGRAPHY] Consumer pokrenut za queue=%s", ORDERSTATUS_CREATED_QUEUE)