import argparse
import io
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image as PILImage
from pymilvus import DataType, MilvusClient

from config import EMBEDDING_DIM, BATCH_SIZE, LAB_COLLECTION, LAB_NLIST, LAB_NPROBE
from services.milvus_service import milvus_service
from services.embedding_service import embedding_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)

_ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(_ROOT, "data", "fashion_lab.parquet")


def _lab_schema(client: MilvusClient):
    schema = client.create_schema(auto_id=True, enable_dynamic_fields=False)
    schema.add_field("id",              DataType.INT64,   is_primary=True)
    schema.add_field("product_id",      DataType.INT64)
    schema.add_field("product_name",    DataType.VARCHAR, max_length=512)
    schema.add_field("gender",          DataType.VARCHAR, max_length=32)
    schema.add_field("master_category", DataType.VARCHAR, max_length=64)
    schema.add_field("sub_category",    DataType.VARCHAR, max_length=64)
    schema.add_field("article_type",    DataType.VARCHAR, max_length=64)
    schema.add_field("base_colour",     DataType.VARCHAR, max_length=64)
    schema.add_field("season",          DataType.VARCHAR, max_length=32)
    schema.add_field("year",            DataType.INT32)
    schema.add_field("usage",           DataType.VARCHAR, max_length=64)
    schema.add_field("has_image",       DataType.BOOL)
    schema.add_field("text_embedding",  DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)
    schema.add_field("image_embedding", DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)
    return schema


def _lab_index_params(client: MilvusClient):
    idx = client.prepare_index_params()
    idx.add_index("id")
    for field in ("gender", "master_category", "article_type", "base_colour", "season", "year"):
        idx.add_index(field, index_type="INVERTED")
    idx.add_index("text_embedding",  index_type="IVF_FLAT", metric_type="COSINE", params={"nlist": LAB_NLIST})
    idx.add_index("image_embedding", index_type="IVF_FLAT", metric_type="COSINE", params={"nlist": LAB_NLIST})
    return idx


def _pil_from_bytes(raw: bytes | None) -> PILImage.Image | None:
    if not raw:
        return None
    try:
        return PILImage.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        return None


def _flush(meta: list[dict], names: list[str], images: list) -> None:
    text_embs = embedding_service.encode_text(names)

    valid_idx, valid_imgs = [], []
    for i, img in enumerate(images):
        if img is not None:
            valid_idx.append(i)
            valid_imgs.append(img)

    valid_embs = []
    if valid_imgs:
        try:
            valid_embs = embedding_service.encode_images(valid_imgs)
        except Exception as exc:
            logger.warning("Image encoding failed (%s) — using zero vectors.", exc)
            valid_embs = [embedding_service.zero_vector()] * len(valid_imgs)

    zero      = embedding_service.zero_vector()
    img_embs  = [zero]  * len(images)
    has_image = [False] * len(images)
    for pos, vi in enumerate(valid_idx):
        img_embs[vi]  = valid_embs[pos]
        has_image[vi] = True

    milvus_service.insert(LAB_COLLECTION, [
        {**m, "has_image": hi, "text_embedding": te, "image_embedding": ie}
        for m, te, ie, hi in zip(meta, text_embs, img_embs, has_image)
    ])


def ingest(data_path: str = DATA_PATH, reset: bool = False) -> None:
    try:
        import pyarrow.parquet as pq
    except ImportError:
        logger.error("pyarrow is not installed.")
        sys.exit(1)

    if not os.path.exists(data_path):
        logger.error("Dataset not found: %s\nRun: python scripts/prepare_lab_data.py", data_path)
        sys.exit(1)

    client = milvus_service.client

    if reset and client.has_collection(LAB_COLLECTION):
        client.drop_collection(LAB_COLLECTION)

    if not client.has_collection(LAB_COLLECTION):
        client.create_collection(
            collection_name=LAB_COLLECTION,
            schema=_lab_schema(client),
            index_params=_lab_index_params(client),
            consistency_level="Strong",
        )

    milvus_service.load_collection(LAB_COLLECTION)

    existing = int(client.get_collection_stats(LAB_COLLECTION).get("row_count", 0))
    if existing > 0:
        logger.info("Collection '%s' already has %d rows — skipping.", LAB_COLLECTION, existing)
        return

    all_rows = pq.read_table(data_path).to_pylist()
    logger.info("Loaded %d rows from %s", len(all_rows), data_path)

    batch_meta, batch_names, batch_images = [], [], []
    total = 0

    for row in all_rows:
        name = (row.get("product_name") or "").strip()[:511]
        if not name:
            continue

        batch_meta.append({
            "product_id":      int(row.get("product_id") or 0),
            "product_name":    name,
            "gender":          str(row.get("gender")          or "")[:31],
            "master_category": str(row.get("master_category") or "")[:63],
            "sub_category":    str(row.get("sub_category")    or "")[:63],
            "article_type":    str(row.get("article_type")    or "")[:63],
            "base_colour":     str(row.get("base_colour")     or "")[:63],
            "season":          str(row.get("season")          or "")[:31],
            "year":            int(row.get("year") or 0),
            "usage":           str(row.get("usage")           or "")[:63],
        })
        batch_names.append(name)
        batch_images.append(_pil_from_bytes(row.get("image_bytes")))

        if len(batch_meta) >= BATCH_SIZE:
            _flush(batch_meta, batch_names, batch_images)
            total += len(batch_meta)
            logger.info("  %d / %d rows inserted ...", total, len(all_rows))
            batch_meta, batch_names, batch_images = [], [], []

    if batch_meta:
        _flush(batch_meta, batch_names, batch_images)
        total += len(batch_meta)

    logger.info("Done — %d rows in '%s'.", total, LAB_COLLECTION)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",  default=DATA_PATH)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    ingest(args.data, args.reset)
