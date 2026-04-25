import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SCIQ_COLLECTION, BATCH_SIZE
from schema.sciq_schema import sciq_schema, sciq_index_params
from services.milvus_service import milvus_service
from services.minilm_embedding_service import minilm_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)

_ROOT            = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH        = os.path.join(_ROOT, "data", "sciq_data.parquet")
SCIQ_INGEST_LIMIT = 500
MIN_SUPPORT_LEN   = 20


def _clean(text: str, max_bytes: int) -> str:
    """Truncate so the UTF-8 byte length stays within max_bytes."""
    encoded = text.strip().encode("utf-8")
    if len(encoded) <= max_bytes:
        return text.strip()
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


def _has_bm25_schema(client) -> bool:
    """Returns True if the existing collection already has the sparse (BM25) field."""
    try:
        info = client.describe_collection(SCIQ_COLLECTION)
        field_names = [f["name"] for f in info.get("fields", [])]
        return "sparse" in field_names
    except Exception:
        return False


def _prepare_collection(reset: bool) -> None:
    client = milvus_service.client

    if client.has_collection(SCIQ_COLLECTION):
        if reset:
            client.drop_collection(SCIQ_COLLECTION)
            logger.info("Dropped collection '%s' (--reset).", SCIQ_COLLECTION)
        elif not _has_bm25_schema(client):
            client.drop_collection(SCIQ_COLLECTION)
            logger.info("Dropped '%s' — outdated schema (no BM25 sparse field), recreating.", SCIQ_COLLECTION)

    if not client.has_collection(SCIQ_COLLECTION):
        client.create_collection(
            collection_name=SCIQ_COLLECTION,
            schema=sciq_schema(client),
            index_params=sciq_index_params(client),
            consistency_level="Strong",
        )
        logger.info("Created collection '%s'.", SCIQ_COLLECTION)

    milvus_service.load_collection(SCIQ_COLLECTION)


def _already_ingested() -> bool:
    stats = milvus_service.client.get_collection_stats(SCIQ_COLLECTION)
    count = int(stats.get("row_count", 0))
    if count > 0:
        logger.info("Collection '%s' already has %d rows — skipping.", SCIQ_COLLECTION, count)
        return True
    return False


def _flush(batch: list[dict], total: int) -> int:
    texts = [r["support_text"] for r in batch]
    embeddings = minilm_service.encode(texts)
    records = [
        {**r, "text_embedding": emb}
        for r, emb in zip(batch, embeddings)
    ]
    milvus_service.insert(SCIQ_COLLECTION, records)
    total += len(records)
    logger.info("  %d rows inserted ...", total)
    return total


def _row_to_record(row: dict, doc_id: int) -> dict | None:
    support = (row.get("support") or "").strip()
    if len(support) < MIN_SUPPORT_LEN:
        return None
    return {
        "doc_id":         doc_id,
        "support_text":   _clean(support, 1999),
        "question":       _clean(str(row.get("question") or ""), 999),
        "correct_answer": _clean(str(row.get("correct_answer") or ""), 499),
        "support_length": len(support), 
    }


def ingest_from_parquet(data_path: str) -> None:
    try:
        import pyarrow.parquet as pq
    except ImportError:
        logger.error("pyarrow is not installed.")
        sys.exit(1)

    logger.info("Loading data from %s ...", data_path)
    rows = pq.read_table(data_path).to_pylist()
    logger.info("Loaded %d rows from parquet.", len(rows))

    batch, total = [], 0
    for row in rows:
        support = (row.get("support_text") or "").strip()
        if len(support) < MIN_SUPPORT_LEN:
            continue
        batch.append({
            "doc_id":         int(row.get("doc_id") or 0),
            "support_text":   _clean(support, 1999),
            "question":       _clean(row.get("question") or "", 999),
            "correct_answer": _clean(row.get("correct_answer") or "", 499),
            "support_length": len(support),
        })
        if len(batch) >= BATCH_SIZE:
            total = _flush(batch, total)
            batch = []

    if batch:
        total = _flush(batch, total)

    logger.info("Done — %d passages in '%s'.", total, SCIQ_COLLECTION)


def ingest_from_stream(limit: int) -> None:
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("datasets package is not installed.  Run: pip install datasets")
        sys.exit(1)

    logger.info("Streaming %d rows from 'allenai/sciq' (train split) ...", limit)
    ds = load_dataset("allenai/sciq", split="train", streaming=True)

    batch, total, doc_id = [], 0, 0
    for row in ds:
        if doc_id >= limit:
            break
        record = _row_to_record(row, doc_id)
        doc_id += 1
        if record is None:
            continue
        batch.append(record)
        if len(batch) >= BATCH_SIZE:
            total = _flush(batch, total)
            batch = []

    if batch:
        total = _flush(batch, total)

    logger.info("Done — %d passages in '%s'.", total, SCIQ_COLLECTION)


def ingest(data_path: str = DATA_PATH, reset: bool = False) -> None:
    _prepare_collection(reset)
    if _already_ingested():
        return

    if os.path.exists(data_path):
        ingest_from_parquet(data_path)
    else:
        logger.info("Parquet not found at %s — falling back to HuggingFace streaming.", data_path)
        ingest_from_stream(SCIQ_INGEST_LIMIT)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",  default=DATA_PATH, help="Path to sciq_data.parquet")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate collection")
    args = parser.parse_args()
    ingest(args.data, args.reset)
