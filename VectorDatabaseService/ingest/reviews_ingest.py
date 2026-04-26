import argparse
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import BATCH_SIZE, REVIEWS_COLLECTION, REVIEWS_MIN_ROWS, REVIEWS_PARQUET_PATH
from schema.reviews_schema import reviews_index_params, reviews_schema
from services.milvus_service import milvus_service
from services.minilm_embedding_service import minilm_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)


def _parse_timestamp(value) -> int:
    if value is None:
        return 0

    if isinstance(value, (int, float)):
        ts = int(value)
        if ts > 10_000_000_000:
            return ts // 1000
        return max(ts, 0)

    text = str(value).strip()
    if not text:
        return 0

    if text.isdigit():
        ts = int(text)
        if ts > 10_000_000_000:
            return ts // 1000
        return max(ts, 0)

    for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return int(datetime.strptime(text, fmt).timestamp())
        except ValueError:
            pass
    return 0


def _prepare_collection(reset: bool) -> None:
    client = milvus_service.client
    if client.has_collection(REVIEWS_COLLECTION) and reset:
        client.drop_collection(REVIEWS_COLLECTION)
        logger.info("Dropped collection '%s' (--reset).", REVIEWS_COLLECTION)

    if not client.has_collection(REVIEWS_COLLECTION):
        client.create_collection(
            collection_name=REVIEWS_COLLECTION,
            schema=reviews_schema(client),
            index_params=reviews_index_params(client),
            consistency_level="Strong",
        )
        logger.info("Created collection '%s'.", REVIEWS_COLLECTION)

    milvus_service.load_collection(REVIEWS_COLLECTION)


def _already_ingested() -> bool:
    stats = milvus_service.client.get_collection_stats(REVIEWS_COLLECTION)
    count = int(stats.get("row_count", 0))
    if count >= REVIEWS_MIN_ROWS:
        logger.info("Collection '%s' already has %d rows - skipping.", REVIEWS_COLLECTION, count)
        return True
    return False


def _flush(batch: list[dict], total: int) -> int:
    texts = [r["review_text"] for r in batch]
    embeddings = minilm_service.encode(texts)

    records = []
    for row, emb in zip(batch, embeddings):
        row["review_embedding"] = emb
        records.append(row)

    result = milvus_service.insert(REVIEWS_COLLECTION, records)
    inserted = result.get("insert_count", len(records))
    total += inserted
    logger.info("Inserted reviews: +%d (total=%d)", inserted, total)
    return total


def ingest(data_path: str = REVIEWS_PARQUET_PATH, reset: bool = False) -> None:
    _prepare_collection(reset)
    if _already_ingested():
        return

    parquet_path = Path(data_path)
    if not parquet_path.exists():
        legacy_path = parquet_path.parent / "book_reviews.parquet"
        if legacy_path.exists():
            parquet_path = legacy_path
        else:
            raise FileNotFoundError(
                f"Reviews parquet not found: {parquet_path} (and fallback {legacy_path})"
            )

    logger.info("Loading reviews from %s", parquet_path)
    rows = pd.read_parquet(parquet_path).to_dict(orient="records")

    batch: list[dict] = []
    total = 0

    for row in rows:
        review_text = str(row.get("review_text") or "")[:6000]
        if not review_text:
            continue

        record = {
            "review_id": str(row.get("review_id") or "")[:64],
            "isbn": str(row.get("isbn") or "")[:32],
            "book_id": int(row.get("book_id") or 0),
            "language": str(row.get("language") or "en")[:32],
            "rating": float(row.get("rating") or 0.0),
            "date_added": _parse_timestamp(row.get("date_added")),
            "n_votes": int(row.get("n_votes") or 0),
            "review_text": review_text,
        }

        if not record["review_id"] or not record["isbn"] or record["book_id"] <= 0:
            continue
        if record["rating"] <= 0:
            continue

        batch.append(record)
        if len(batch) >= BATCH_SIZE:
            total = _flush(batch, total)
            batch = []

    if batch:
        total = _flush(batch, total)

    logger.info("Reviews ingest done. Total inserted=%d", total)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest reviews into Milvus")
    parser.add_argument("--data", default=REVIEWS_PARQUET_PATH, help="Path to reviews parquet")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate collection")
    args = parser.parse_args()
    ingest(data_path=args.data, reset=args.reset)
