"""
Lab ingestion — collection: fashion_lab (1,000 rows, streaming).
================================================================
Designed for laboratory sessions where disk quota is limited
and demo session time is short. Uses the same dataset and CLIP embeddings
as the full ingestion, but features:

  - Only 1,000 rows (sufficient diversity for all query types)
  - Streaming mode ENABLED by default (dataset is never written to disk)
  - Dedicated collection name: fashion_lab
  - NLIST = 64 (smaller index tailored to the reduced row count)
"""

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymilvus import DataType, MilvusClient
from config import MILVUS_URI, EMBEDDING_DIM, BATCH_SIZE, LAB_COLLECTION, LAB_NLIST, LAB_NPROBE
from services.milvus_service import milvus_service
from services.embedding_service import embedding_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)

LAB_DEFAULT_ROWS = 1_000

def _lab_schema(client: MilvusClient):
    schema = client.create_schema(
        auto_id=True,
        enable_dynamic_fields=False,
        description=(
            "Lab podskup dataseta ashraq/fashion-product-images-small (1 000 redova). "
            "CLIP ViT-B/32 embeddinzi — tekst i slika u istom 512-dim prostoru."
        ),
    )
    schema.add_field("id",             DataType.INT64,   is_primary=True)
    schema.add_field("product_id",     DataType.INT64)
    schema.add_field("product_name",   DataType.VARCHAR, max_length=512)
    schema.add_field("gender",         DataType.VARCHAR, max_length=32)
    schema.add_field("master_category",DataType.VARCHAR, max_length=64)
    schema.add_field("sub_category",   DataType.VARCHAR, max_length=64)
    schema.add_field("article_type",   DataType.VARCHAR, max_length=64)
    schema.add_field("base_colour",    DataType.VARCHAR, max_length=64)
    schema.add_field("season",         DataType.VARCHAR, max_length=32)
    schema.add_field("year",           DataType.INT32)
    schema.add_field("usage",          DataType.VARCHAR, max_length=64)
    schema.add_field("has_image",      DataType.BOOL)
    schema.add_field("text_embedding", DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)
    schema.add_field("image_embedding",DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)
    return schema


def _lab_index_params(client: MilvusClient):
    idx = client.prepare_index_params()
    idx.add_index("id")
    idx.add_index("gender",           index_type="Trie")
    idx.add_index("master_category",  index_type="Trie")
    idx.add_index("article_type",     index_type="Trie")
    idx.add_index("base_colour",      index_type="Trie")
    idx.add_index("season",           index_type="Trie")
    idx.add_index("year",             index_type="STL_SORT")
    idx.add_index(
        "text_embedding",
        index_type="IVF_FLAT", metric_type="COSINE",
        params={"nlist": LAB_NLIST},
    )
    idx.add_index(
        "image_embedding",
        index_type="IVF_FLAT", metric_type="COSINE",
        params={"nlist": LAB_NLIST},
    )
    return idx


def _safe_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _safe_str(v, max_len=64):
    return str(v).strip()[:max_len] if v is not None else ""


def _flush(meta, names, images):
    text_embs = embedding_service.encode_text(names)

    valid_idx, valid_imgs = [], []
    for i, img in enumerate(images):
        if img is not None:
            valid_idx.append(i)
            valid_imgs.append(img)

    if valid_imgs:
        try:
            valid_embs = embedding_service.encode_images(valid_imgs)
        except Exception as exc:
            logger.warning("Image encoding error (%s) — using zero vectors.", exc)
            valid_embs = [embedding_service.zero_vector()] * len(valid_imgs)
    else:
        valid_embs = []

    zero = embedding_service.zero_vector()
    img_embs  = [zero] * len(images)
    has_image = [False] * len(images)
    for pos, vi in enumerate(valid_idx):
        img_embs[vi]  = valid_embs[pos]
        has_image[vi] = True

    records = [
        {**m, "has_image": hi, "text_embedding": te, "image_embedding": ie}
        for m, te, ie, hi in zip(meta, text_embs, img_embs, has_image)
    ]
    milvus_service.insert(LAB_COLLECTION, records)


def ingest(limit: int = LAB_DEFAULT_ROWS, reset: bool = False) -> None:
    """
    Umetanje `limit` redova iz ashraq/fashion-product-images-small
    u kolekciju fashion_lab. Uvek koristi streaming — bez disk keša.
    """
    from datasets import load_dataset

    client = milvus_service.client
    schema = _lab_schema(client)
    idx    = _lab_index_params(client)

    if reset:
        if client.has_collection(LAB_COLLECTION):
            client.drop_collection(LAB_COLLECTION)
            logger.info("Dropped '%s'.", LAB_COLLECTION)
        client.create_collection(
            collection_name=LAB_COLLECTION,
            schema=schema,
            index_params=idx,
            consistency_level="Strong",
        )
        logger.info("Recreated '%s'.", LAB_COLLECTION)
    else:
        if not client.has_collection(LAB_COLLECTION):
            client.create_collection(
                collection_name=LAB_COLLECTION,
                schema=schema,
                index_params=idx,
                consistency_level="Strong",
            )
            logger.info("Created '%s'.", LAB_COLLECTION)

    milvus_service.load_collection(LAB_COLLECTION)

    existing = int(client.get_collection_stats(LAB_COLLECTION).get("row_count", 0))
    if existing > 0:
        logger.info(
            "'%s' already has %d rows — skipping.  Use --reset to re-ingest.",
            LAB_COLLECTION, existing,
        )
        return

    logger.info("Streaming dataset (limit=%d, no disk cache) …", limit)
    ds = load_dataset(
        "ashraq/fashion-product-images-small",
        split="train",
        streaming=True,
    )

    batch_meta, batch_names, batch_images = [], [], []
    total_inserted = 0

    for i, row in enumerate(ds):
        if i >= limit:
            break

        name = _safe_str(row.get("productDisplayName"), 511)
        if not name:
            continue

        pil_img = row.get("image")
        if pil_img is not None:
            try:
                pil_img = pil_img.convert("RGB")
            except Exception:
                pil_img = None

        batch_meta.append({
            "product_id":      _safe_int(row.get("id")),
            "product_name":    name,
            "gender":          _safe_str(row.get("gender"), 31),
            "master_category": _safe_str(row.get("masterCategory"), 63),
            "sub_category":    _safe_str(row.get("subCategory"), 63),
            "article_type":    _safe_str(row.get("articleType"), 63),
            "base_colour":     _safe_str(row.get("baseColour"), 63),
            "season":          _safe_str(row.get("season"), 31),
            "year":            _safe_int(row.get("year")),
            "usage":           _safe_str(row.get("usage"), 63),
        })
        batch_names.append(name)
        batch_images.append(pil_img)

        if len(batch_meta) >= BATCH_SIZE:
            _flush(batch_meta, batch_names, batch_images)
            total_inserted += len(batch_meta)
            logger.info("  %d / %d rows inserted …", total_inserted, limit)
            batch_meta, batch_names, batch_images = [], [], []

    if batch_meta:
        _flush(batch_meta, batch_names, batch_images)
        total_inserted += len(batch_meta)

    logger.info("Done — %d rows in '%s'.", total_inserted, LAB_COLLECTION)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unos lab podskupa u kolekciju fashion_lab.")
    parser.add_argument("--limit", type=int, default=LAB_DEFAULT_ROWS,
                        help=f"Broj redova za unos (podrazumevano: {LAB_DEFAULT_ROWS})")
    parser.add_argument("--reset", action="store_true",
                        help="Briše i ponovo kreira kolekciju pre unosa")
    args = parser.parse_args()
    ingest(limit=args.limit, reset=args.reset)
