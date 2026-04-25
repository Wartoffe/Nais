"""Book-reviews ingestion.

Idempotent: no-op if the collection already holds >= REVIEWS_MIN_ROWS rows.
Prerequisite: books collection must exist and be populated (run books_ingest first).

Generation strategy
-------------------
For each book fetched from Milvus we generate REVIEWS_PER_BOOK (default: 2)
synthetic reviews.  Rating distribution and review text are derived
deterministically from the book's ISBN so repeated runs produce
the same content (safe to drop-and-reingest without drift).
"""

import argparse
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    BATCH_SIZE,
    BOOK_REVIEWS_COLLECTION,
    BOOKS_COLLECTION,
    REVIEWS_MIN_ROWS,
    REVIEWS_PER_BOOK,
)
from schema.reviews_schema import reviews_index_params, reviews_schema
from services.milvus_service import milvus_service
from services.minilm_embedding_service import minilm_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)

_USER_TYPES = ["verified_buyer", "critic", "casual_reader", "enthusiast", "librarian"]

_POSITIVE = [
    "Absolutely loved '{title}'. The storytelling is captivating and the characters feel real. "
    "Highly recommend to anyone who enjoys {genre}.",
    "'{title}' exceeded my expectations. A beautifully written piece that kept me engaged from start to finish.",
    "One of the best books I've read this year. '{title}' offers a fresh perspective and a compelling narrative.",
    "A masterpiece in its genre. '{title}' is thoughtfully crafted with rich detail and emotional depth.",
    "Could not put this down. '{title}' has perfect pacing and exceptional world-building.",
]
_NEUTRAL = [
    "'{title}' is a solid read — nothing groundbreaking, but well written and enjoyable for fans of {genre}.",
    "Decent book overall. '{title}' has its moments but also feels slow in places. Worth a read.",
    "'{title}' is competent and entertaining. I'd pick it up again, though it didn't leave a lasting impression.",
    "An average entry in the {genre} genre. '{title}' gets the job done without particularly standing out.",
    "Mixed feelings about '{title}'. Some parts were genuinely engaging while others felt rushed.",
]
_NEGATIVE = [
    "Disappointed with '{title}'. The plot felt predictable and the characters were underdeveloped.",
    "'{title}' had a promising premise but failed to deliver. The pacing drags significantly in the second half.",
    "Not for me. '{title}' felt overhyped and I struggled to connect with the narrative.",
    "'{title}' had potential but the execution was lacking. The ending especially felt unearned.",
    "Wouldn't recommend '{title}'. The writing felt inconsistent and the story lost direction halfway through.",
]


# ── collection lifecycle ──────────────────────────────────────────────────────

def _prepare_collection(reset: bool) -> None:
    client = milvus_service.client

    if client.has_collection(BOOK_REVIEWS_COLLECTION):
        if reset:
            client.drop_collection(BOOK_REVIEWS_COLLECTION)
            logger.info("Dropped collection '%s' (--reset).", BOOK_REVIEWS_COLLECTION)

    if not client.has_collection(BOOK_REVIEWS_COLLECTION):
        client.create_collection(
            collection_name=BOOK_REVIEWS_COLLECTION,
            schema=reviews_schema(client),
            index_params=reviews_index_params(client),
            consistency_level="Strong",
        )
        logger.info("Created collection '%s'.", BOOK_REVIEWS_COLLECTION)

    milvus_service.load_collection(BOOK_REVIEWS_COLLECTION)


def _already_ingested() -> bool:
    stats = milvus_service.client.get_collection_stats(BOOK_REVIEWS_COLLECTION)
    count = int(stats.get("row_count", 0))
    if count >= REVIEWS_MIN_ROWS:
        logger.info(
            "Collection '%s' already has %d rows — skipping.",
            BOOK_REVIEWS_COLLECTION, count,
        )
        return True
    return False


# ── book fetching ─────────────────────────────────────────────────────────────

def _fetch_all_books() -> list[dict]:
    """Page through the books collection and return isbn + title + genre for every row."""
    client    = milvus_service.client
    page_size = 200
    results, offset = [], 0

    while True:
        batch = client.query(
            collection_name=BOOKS_COLLECTION,
            filter="",
            output_fields=["id", "isbn", "title", "genre", "goodreads_id"],
            limit=page_size,
            offset=offset,
        )
        if not batch:
            break
        results.extend(batch)
        offset += len(batch)
        if len(batch) < page_size:
            break

    logger.info("Fetched %d books from '%s'.", len(results), BOOKS_COLLECTION)
    return results


# ── review generation ─────────────────────────────────────────────────────────

def _generate_reviews(book: dict, count: int) -> list[dict]:
    """Return ``count`` deterministic synthetic reviews for *book*.

    Using ``random.Random(isbn)`` guarantees the same output for the
    same book across multiple ingest runs.
    """
    isbn  = (book.get("isbn") or "unknown")
    title = (book.get("title") or "this book")
    genre = (book.get("genre") or "")
    book_id = str(book.get("goodreads_id") or isbn)
    rng   = random.Random(isbn)          # per-book seed → deterministic

    reviews = []
    for i in range(count):
        rating = rng.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 35, 30])[0]

        if rating >= 4:
            template = rng.choice(_POSITIVE)
        elif rating == 3:
            template = rng.choice(_NEUTRAL)
        else:
            template = rng.choice(_NEGATIVE)

        text      = template.format(title=title, genre=genre)
        days_ago  = rng.randint(0, 365 * 3)
        created   = (datetime.utcnow() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        reviews.append({
            "review_id":   f"{isbn}-{i + 1}-{uuid.uuid4().hex[:8]}"[:64],
            "isbn":        isbn[:32],
            "book_id":     book_id[:64],
            "rating":      rating,
            "date_added":  created[:64],
            "n_votes":     rng.randint(0, 250),
            "user_type":   rng.choice(_USER_TYPES)[:32],
            "created_at":  created[:64],
            "review_text": text[:4000],
        })

    return reviews


# ── flush helper ─────────────────────────────────────────────────────────────

def _flush(batch: list[dict], total: int) -> int:
    """Encode review_text → review_embedding and insert the batch."""
    texts      = [r["review_text"] for r in batch]
    embeddings = minilm_service.encode(texts)
    records    = [{**r, "review_embedding": emb} for r, emb in zip(batch, embeddings)]
    milvus_service.insert(BOOK_REVIEWS_COLLECTION, records)
    total += len(records)
    logger.info("  %d reviews inserted ...", total)
    return total


# ── entry point ───────────────────────────────────────────────────────────────

def ingest(reset: bool = False) -> None:
    _prepare_collection(reset)
    if _already_ingested():
        return

    client = milvus_service.client
    if not client.has_collection(BOOKS_COLLECTION):
        logger.error(
            "Books collection '%s' not found.  Run books_ingest.py first.",
            BOOKS_COLLECTION,
        )
        sys.exit(1)

    books = _fetch_all_books()
    if not books:
        logger.error(
            "No books found in '%s'.  Run books_ingest.py first.",
            BOOKS_COLLECTION,
        )
        sys.exit(1)

    batch, total = [], 0
    for book in books:
        for review in _generate_reviews(book, count=REVIEWS_PER_BOOK):
            batch.append(review)
            if len(batch) >= BATCH_SIZE:
                total = _flush(batch, total)
                batch = []

    if batch:
        total = _flush(batch, total)

    logger.info(
        "Done — %d reviews (%d per book) in '%s'.",
        total, REVIEWS_PER_BOOK, BOOK_REVIEWS_COLLECTION,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest book reviews into Milvus")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate collection")
    args = parser.parse_args()
    ingest(args.reset)