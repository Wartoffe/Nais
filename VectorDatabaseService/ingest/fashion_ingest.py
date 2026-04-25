"""
Multimodal ingestion of fashion products into Milvus.

Dataset: ashraq/fashion-product-images-small (HuggingFace)

Modalities:
- TEXT:  productDisplayName  ->  CLIP text encoder  ->  text_embedding
- IMAGE: photo (PIL)         ->  CLIP image encoder ->  image_embedding

Both vectors reside in the same 512-dimensional CLIP space, 
enabling cross-modal retrieval.
"""

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image as PILImage

from config import FASHION_COLLECTION, BATCH_SIZE, MAX_INGEST_COUNT
from schema.milvus_schema import fashion_schema, fashion_index_params
from services.milvus_service import milvus_service
from services.embedding_service import embedding_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_str(value, max_len: int = 64) -> str:
    if value is None:
        return ""
    return str(value).strip()[:max_len]


def _build_metadata(row: dict) -> dict:
    return {
        "product_id":      _safe_int(row.get("id")),
        "product_name":    _safe_str(row.get("productDisplayName"), 511),
        "gender":          _safe_str(row.get("gender"), 31),
        "master_category": _safe_str(row.get("masterCategory"), 63),
        "sub_category":    _safe_str(row.get("subCategory"), 63),
        "article_type":    _safe_str(row.get("articleType"), 63),
        "base_colour":     _safe_str(row.get("baseColour"), 63),
        "season":          _safe_str(row.get("season"), 31),
        "year":            _safe_int(row.get("year")),
        "usage":           _safe_str(row.get("usage"), 63),
    }


def ingest(limit: int = MAX_INGEST_COUNT, reset: bool = False, stream: bool = False) -> None:
    """
    Pun multimodalni ingestion pipeline.

    Koraci:
      1. Obezbedi (ili resetuj) Milvus kolekciju i indekse.
      2. Učitaj HuggingFace dataset (keširano ili streaming).
      3. Za svaki batch:
           a. Enkoduj nazive proizvoda  → text_embedding   (CLIP text tower)
           b. Enkoduj fotografije       → image_embedding  (CLIP image tower)
              Ako slika nedostaje/oštećena → nulti vektor + has_image=False
      4. Umetni batch u Milvus.

    Oba vektora su 512-dim i L2-normalizovana — cosine sličnost = skalarni proizvod.

    stream=True: dataset se uzima red-po-red sa HuggingFace bez upisivanja
                 ~1.8 GB na disk — idealno za mašine sa malim disk kvotama.
    """
    from datasets import load_dataset  # lazy import — nije potreban pri pokretanju API-ja

    client = milvus_service.client
    schema = fashion_schema(client)
    idx    = fashion_index_params(client)

    if reset:
        milvus_service.drop_and_recreate(FASHION_COLLECTION, schema, idx)
    else:
        milvus_service.ensure_collection(FASHION_COLLECTION, schema, idx)

    milvus_service.load_collection(FASHION_COLLECTION)

    # Idempotentnost: preskočiti ako je već popunjeno
    stats    = milvus_service.collection_stats(FASHION_COLLECTION)
    existing = int(stats.get("row_count", 0))
    if existing > 0:
        logger.info(
            "Collection '%s' already has %d rows — skipping. "
            "Re-run with --reset to force re-ingestion.",
            FASHION_COLLECTION, existing,
        )
        return

    if stream:
        logger.info("Streaming dataset 'ashraq/fashion-product-images-small' (no disk cache) …")
        ds = load_dataset("ashraq/fashion-product-images-small", split="train", streaming=True)
        total_to_ingest = limit
        logger.info("Streaming mode — will ingest up to %d rows.", total_to_ingest)
    else:
        logger.info("Loading dataset 'ashraq/fashion-product-images-small' …")
        ds = load_dataset("ashraq/fashion-product-images-small", split="train")
        total_available = len(ds)
        total_to_ingest = min(limit, total_available)
        logger.info("Dataset ready — %d rows available, ingesting up to %d.", total_available, total_to_ingest)

    batch_meta:   list[dict] = []
    batch_names:  list[str]  = []
    batch_images: list       = []   # PILImage.Image | None
    total_inserted = 0

    for i, row in enumerate(ds):
        if i >= total_to_ingest:
            break

        name = _safe_str(row.get("productDisplayName"), 511)
        if not name:
            continue   # preskočiti redove bez naziva proizvoda

        pil_img = row.get("image")   # PIL.Image.Image ili None iz HF datasets
        if pil_img is not None:
            try:
                pil_img = pil_img.convert("RGB")
            except Exception:
                pil_img = None

        batch_meta.append(_build_metadata(row))
        batch_names.append(name)
        batch_images.append(pil_img)

        if len(batch_meta) >= BATCH_SIZE:
            _flush_batch(batch_meta, batch_names, batch_images)
            total_inserted += len(batch_meta)
            logger.info("Inserted %d / %d …", total_inserted, total_to_ingest)
            batch_meta, batch_names, batch_images = [], [], []

    if batch_meta:
        _flush_batch(batch_meta, batch_names, batch_images)
        total_inserted += len(batch_meta)

    logger.info(
        "Ingestion complete — %d rows inserted into '%s'.",
        total_inserted, FASHION_COLLECTION,
    )


def _flush_batch(meta, names, images) -> None:
    """
    Enkoduje jedan batch (naziv, slika) parova i upisuje u Milvus.

    Enkodovanje teksta : uvek uspešno.
    Enkodovanje slika  : grupno enkodovanje validnih slika; nulti vektor za None.
    """
    # Tekst embeddinzi (uvek prisutni)
    text_embs = embedding_service.encode_text(names)

    # Razdvajanje validnih i nedostajućih slika
    valid_idx:  list[int] = []
    valid_imgs: list      = []
    for idx, img in enumerate(images):
        if img is not None:
            valid_idx.append(idx)
            valid_imgs.append(img)

    # Grupno enkodovanje validnih slika
    valid_embs: list[list[float]] = []
    if valid_imgs:
        try:
            valid_embs = embedding_service.encode_images(valid_imgs)
        except Exception as exc:
            logger.warning("Image encoding failed (%s) — using zero vectors.", exc)
            valid_embs = [embedding_service.zero_vector()] * len(valid_imgs)

    # Ponovo sastavljanje pune liste image_embs (nule tamo gde slika nije bila)
    zero = embedding_service.zero_vector()
    image_embs     = [zero] * len(images)
    has_image_list = [False] * len(images)
    for pos, vi in enumerate(valid_idx):
        image_embs[vi]     = valid_embs[pos]
        has_image_list[vi] = True

    records = []
    for m, te, ie, hi in zip(meta, text_embs, image_embs, has_image_list):
        records.append({**m, "has_image": hi, "text_embedding": te, "image_embedding": ie})

    milvus_service.insert(FASHION_COLLECTION, records)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Umetanje modnih proizvoda (tekst + slike) u Milvus."
    )
    parser.add_argument("--limit", type=int, default=MAX_INGEST_COUNT,
                        help="Maksimalan broj redova za ingestion (podrazumevano: ceo dataset)")
    parser.add_argument("--reset", action="store_true",
                        help="Briše i ponovo kreira kolekciju pre ingestion-a")
    parser.add_argument("--stream", action="store_true",
                        help="Stream dataset sa HuggingFace bez kešovanja na disk (~1.8 GB uštede)")
    args = parser.parse_args()
    ingest(limit=args.limit, reset=args.reset, stream=args.stream)
