import argparse
import base64
import logging
from pathlib import Path

import pandas as pd

from config import BATCH_SIZE, BOOKS_COLLECTION, BOOKS_MIN_ROWS, BOOKS_PARQUET_PATH
from schema.books_schema import books_index_params, books_schema
from services.embedding_service import embedding_service
from services.milvus_service import milvus_service
from services.minilm_embedding_service import minilm_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)


def _normalize_bytes_to_b64(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (bytes, bytearray)):
        return base64.b64encode(bytes(value)).decode("utf-8")
    if isinstance(value, str):
        stripped = value.strip()
        return stripped
    return ""


def _prepare_collection(reset: bool) -> None:
    client = milvus_service.client
    if client.has_collection(BOOKS_COLLECTION) and reset:
        client.drop_collection(BOOKS_COLLECTION)
        logger.info("Dropped collection '%s' (--reset).", BOOKS_COLLECTION)

    if not client.has_collection(BOOKS_COLLECTION):
        client.create_collection(
            collection_name=BOOKS_COLLECTION,
            schema=books_schema(client),
            index_params=books_index_params(client),
            consistency_level="Strong",
        )
        logger.info("Created collection '%s'.", BOOKS_COLLECTION)

    milvus_service.load_collection(BOOKS_COLLECTION)


def _already_ingested() -> bool:
    stats = milvus_service.client.get_collection_stats(BOOKS_COLLECTION)
    count = int(stats.get("row_count", 0))
    if count >= BOOKS_MIN_ROWS:
        logger.info("Collection '%s' already has %d rows - skipping.", BOOKS_COLLECTION, count)
        return True
    return False


def _cover_embedding(row: dict) -> tuple[list[float], bool]:
    image_bytes = row.get("image_bytes")
    cover_url = (row.get("coverImg") or "").strip()

    if image_bytes:
        try:
            raw = base64.b64decode(image_bytes)
            return embedding_service.encode_from_bytes(raw), True
        except Exception:
            pass

    if cover_url:
        try:
            return embedding_service.encode_from_url(cover_url), True
        except Exception:
            pass

    return embedding_service.zero_vector(), False


def _flush(batch: list[dict], total: int) -> int:
    texts = [r["description"] for r in batch]
    text_embeddings = minilm_service.encode(texts)

    records = []
    for row, desc_vec in zip(batch, text_embeddings):
        cover_vec, has_image = _cover_embedding(row)
        records.append(
            {
                "goodreads_id": row["goodreads_id"],
                "isbn": row["isbn"],
                "title": row["title"],
                "author": row["author"],
                "description": row["description"],
                "language": row["language"],
                "coverImg": row["coverImg"],
                "publisher": row["publisher"],
                "pages": row["pages"],
                "has_image": bool(row.get("has_image", False) and has_image),
                "description_embedding": desc_vec,
                "cover_embedding": cover_vec,
            }
        )

    result = milvus_service.insert(BOOKS_COLLECTION, records)
    inserted = result.get("insert_count", len(records))
    total += inserted
    logger.info("Inserted books: +%d (total=%d)", inserted, total)
    return total


def ingest(data_path: str = BOOKS_PARQUET_PATH, reset: bool = False) -> None:
    _prepare_collection(reset)
    if _already_ingested():
        return

    parquet_path = Path(data_path)
    if not parquet_path.exists():
        raise FileNotFoundError(f"Books parquet not found: {parquet_path}")

    logger.info("Loading books from %s", parquet_path)
    rows = pd.read_parquet(parquet_path).to_dict(orient="records")

    batch: list[dict] = []
    total = 0

    for i, row in enumerate(rows, start=1):
        record = {
            "goodreads_id": int(row.get("goodreads_id") or 0),
            "isbn": str(row.get("isbn") or "")[:32],
            "title": str(row.get("title") or "")[:512],
            "author": str(row.get("author") or "")[:256],
            "description": str(row.get("description") or "")[:6000],
            "language": str(row.get("language") or "en")[:32],
            "coverImg": str(row.get("coverImg") or "")[:2048],
            "publisher": str(row.get("publisher") or "")[:256],
            "pages": int(row.get("pages") or 0),
            # image_bytes is only a transient ingest input, never persisted in Milvus
            "image_bytes": _normalize_bytes_to_b64(row.get("image_bytes")),
            "has_image": bool(row.get("has_image", False)),
        }

        if not record["isbn"] or not record["title"] or not record["description"]:
            continue

        batch.append(record)
        if len(batch) >= BATCH_SIZE:
            total = _flush(batch, total)
            batch = []

    if batch:
        total = _flush(batch, total)

    logger.info("Books ingest done. Total inserted=%d", total)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest books into Milvus")
    parser.add_argument("--data", default=BOOKS_PARQUET_PATH, help="Path to books parquet")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate collection")
    args = parser.parse_args()
    ingest(data_path=args.data, reset=args.reset)
