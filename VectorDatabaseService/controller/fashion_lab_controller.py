"""
Lab controller for operations on the fashion_lab collection (1 000 rows).

Collection : fashion_lab  (1 000 rows, CLIP ViT-B/32, 512-dim)
Prefix     : /lab/v1/fashion

Phase 1 - CRUD
  POST   /products          Insert a single product (text is encoded automatically)
  GET    /products          List products with optional scalar filter
  GET    /products/{id}     Fetch a single product by Milvus ID
  DELETE /products/{id}     Delete a single product

Phase 2 - Semantic text search
  GET /search/text          Encode text query -> search text_embedding
                            Concept: ANN search, cosine similarity

Phase 3 - Filtered search
  GET /search/filtered      Text query + optional filter by gender/colour/category
                            Concept: pre-filtering before ANN search

Phase 4 - Image search
  POST /search/image        Image URL -> encode -> search image_embedding
                            Concept: visual similarity search

Phase 5 - Cross-modal search
  GET  /search/cross/text-to-image    Text query  -> image_embedding
  POST /search/cross/image-to-text    Image URL   -> text_embedding
                            Concept: CLIP shared space, cross-modal retrieval

Phase 6 - Combined (multimodal fusion)
  POST /search/multimodal   Text + image URL -> weighted score fusion
                            Concept: combining modalities, RRF fusion

Utility
  GET /stats                Collection statistics for fashion_lab
"""

import io
import logging
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Query, UploadFile
from PIL import Image as PILImage
from pydantic import BaseModel, Field

from model.fashion_product import FashionProductBase
from service.impl.fashion_lab_service import fashion_lab_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lab/v1/fashion", tags=["Lab - Multimodal Fashion (1k rows)"])

TOP_K_DEFAULT = 5

class ImageSearchRequest(BaseModel):
    """Request body for image search (lab)."""
    url:   str = Field(..., description="Public image URL to use as the query")
    top_k: int = Field(TOP_K_DEFAULT, ge=1, le=20)


class BatchSearchRequest(BaseModel):
    """Request body for batch search over multiple queries at once."""
    queries:  list[str] = Field(..., min_length=1, max_length=10, description="List of queries (max 10)")
    top_k:    int        = Field(TOP_K_DEFAULT, ge=1, le=20)


class MultimodalRequest(BaseModel):
    """Request body for multimodal fusion (lab)."""
    text:        str   = Field(..., description="Text component of the query")
    image_url:   str   = Field(..., description="Image URL as the visual component")
    text_weight: float = Field(0.5, ge=0.0, le=1.0, description="0 = image only, 1 = text only")
    top_k:       int   = Field(TOP_K_DEFAULT, ge=1, le=20)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 - CRUD
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/products", summary="[Phase 1] Insert a single product")
def create_product(body: FashionProductBase):
    """
    Insert a single product.
    The product name is automatically encoded with the CLIP text tower -> text_embedding.
    image_embedding is set to a zero vector (no image URL is provided on insert).
    """
    return fashion_lab_service.create_product(body)


@router.post("/products/batch", summary="[Phase 1] Batch insert multiple products")
def create_products_batch(body: list[FashionProductBase]):
    """
    CONCEPT: Efficient batch insert.

    Difference from single insert:
      - All names are encoded in a SINGLE model call (batch_size=32)
      - All records are inserted in a SINGLE Milvus insert call
      - Significantly faster than N individual POST /products calls

    Try: send a list of 5-10 products and observe that
    insert_count equals the number of objects sent.
    """
    try:
        return fashion_lab_service.create_products_batch(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/products", summary="[Phase 1] List products (scalar filter)")
def list_products(
    gender:   Optional[str] = Query(None, description="Filter by gender"),
    colour:   Optional[str] = Query(None, description="Filter by base_colour"),
    category: Optional[str] = Query(None, description="Filter by master_category"),
    limit:    int            = Query(10, ge=1, le=100),
    offset:   int            = Query(0, ge=0),
):
    """
    Pure scalar search - no vector ranking.
    Demonstrates Milvus scalar filters (equivalent to a SQL WHERE clause).
    """
    rows = fashion_lab_service.list_products(gender, colour, category, limit, offset)
    return {"count": len(rows), "results": rows}


@router.get("/products/{product_id}", summary="[Phase 1] Fetch product by Milvus ID")
def get_product(product_id: int):
    """Fetches a single product by its auto-generated Milvus ID."""
    try:
        return fashion_lab_service.get_product(product_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.delete("/products/{product_id}", summary="[Phase 1] Delete product by Milvus ID")
def delete_product(product_id: int):
    """Deletes a product by Milvus ID."""
    return fashion_lab_service.delete_product(product_id)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 - Semantic text search
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/search/text", summary="[Phase 2] Semantic text search")
def text_search(
    query: str = Query(..., description="Natural language query, e.g. 'blue casual jeans'"),
    top_k: int = Query(TOP_K_DEFAULT, ge=1, le=20),
):
    """
    CONCEPT: ANN search with cosine similarity.

    Steps:
      1. CLIP text tower encodes the query -> 512-dim vector
      2. Milvus IVF_FLAT index finds the nearest neighbors in text_embedding
      3. Results ranked by cosine similarity (1.0 = identical, 0.0 = unrelated)

    Try: "blue denim jeans", "summer dress women", "white sports shoes"
    """
    results = fashion_lab_service.text_search(query, top_k)
    return {"query": query, "modality": "text -> text_embedding", "results": results}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 - Filtered search
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/search/filtered", summary="[Phase 3] Text search with scalar pre-filter")
def filtered_search(
    query:    str            = Query(..., description="Text query"),
    gender:   Optional[str] = Query(None, description="Pre-filter: Men | Women | Boys | Girls"),
    colour:   Optional[str] = Query(None, description="Pre-filter: Blue | Red | Black | ..."),
    category: Optional[str] = Query(None, description="Pre-filter: Apparel | Footwear | ..."),
    top_k:    int            = Query(TOP_K_DEFAULT, ge=1, le=20),
):
    """
    CONCEPT: Pre-filtering before ANN search.

    Milvus applies the scalar WHERE clause FIRST (using Trie/STL_SORT indexes),
    then runs ANN search only within the filtered subset.
    This is faster and more precise than post-filtering.

    Try: query="casual shirt", gender="Men"
    """
    results = fashion_lab_service.filtered_search(query, gender, colour, category, top_k)
    return {
        "query":    query,
        "modality": "text -> text_embedding (pre-filtered)",
        "results":  results,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3b - Hybrid search (both vector fields simultaneously)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/search/hybrid", summary="[Phase 3b] Hybrid search - both vector fields simultaneously")
def hybrid_search(
    query: str = Query(..., description="Text query"),
    top_k: int = Query(TOP_K_DEFAULT, ge=1, le=20),
):
    """
    CONCEPT: Milvus AnnSearchRequest - simultaneous search across multiple vector fields.

    Difference from /search/multimodal:
      - Multimodal: 2 separate search calls + Python RRF in memory
      - Hybrid:     1 Milvus hybrid_search call, RRF inside Milvus

    The same text query is encoded once and searched in BOTH fields:
      text_embedding  -> finds semantically similar names
      image_embedding -> finds visually similar photos (cross-modal)

    Milvus internally fuses the ranks using RRF(k=60) and returns a single
    unified ranked list. This is native Milvus 2.x multi-vector search.

    Try: "blue jeans Men" - observe the difference in results vs /search/text
    """
    try:
        results = fashion_lab_service.hybrid_text_search(query, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "query":    query,
        "modality": "text -> [text_embedding + image_embedding] (Milvus hybrid_search)",
        "results":  results,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3c - Search parameter tuning
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/search/tuning", summary="[Phase 3c] Parameter tuning - nprobe demo")
def search_tuning(
    query:  str = Query(..., description="Text query"),
    nprobe: int = Query(16, ge=1, le=64, description="Number of clusters to search (1=fast/inaccurate, 64=slow/accurate)"),
    top_k:  int = Query(TOP_K_DEFAULT, ge=1, le=20),
):
    """
    CONCEPT: IVF_FLAT nprobe tuning - trade-off between speed and accuracy.

    IVF_FLAT partitions the vector space into nlist=64 clusters (Voronoi cells).
    During search, nprobe determines how many clusters are scanned:

      nprobe=1  -> only the nearest cluster  -> fastest, may miss relevant results
      nprobe=16 -> 16 clusters (default)     -> good balance (25% of space)
      nprobe=64 -> all clusters              -> equivalent to brute-force, most accurate

    Try the same query with nprobe=1, 8, 16, 32, 64 and observe:
      - Changes in result ordering (accuracy)
      - Changes in score values
    The collection has only 1000 rows so speed differences will not be visible,
    but differences in results may appear.
    """
    try:
        results = fashion_lab_service.search_with_tuning(query, nprobe, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "query":        query,
        "nprobe":       nprobe,
        "nlist":        64,
        "coverage_pct": round(nprobe / 64 * 100, 1),
        "modality":     "text -> text_embedding (IVF_FLAT, custom nprobe)",
        "results":      results,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4 - Image search
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/search/image", summary="[Phase 4] Visual similarity search")
def image_search(body: ImageSearchRequest):
    """
    CONCEPT: Visual similarity search.

    Steps:
      1. Image is fetched from the URL and decoded via Pillow
      2. CLIP image tower encodes it -> 512-dim vector
      3. Milvus IVF_FLAT finds the nearest neighbors in image_embedding

    Results are products whose PHOTOS visually resemble the query image.
    """
    try:
        results = fashion_lab_service.image_search(body.url, body.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "image_url": body.url,
        "modality":  "image -> image_embedding",
        "results":   results,
    }


@router.post("/search/image/by-upload", summary="[Phase 4] Visual similarity search (file upload)")
async def image_search_upload(
    file:  UploadFile,
    top_k: int = Query(TOP_K_DEFAULT, ge=1, le=20),
):
    """
    Same as /search/image but accepts a local file instead of a URL.
    Use this for testing with images from your local machine.
    """
    try:
        contents = await file.read()
        img = PILImage.open(io.BytesIO(contents)).convert("RGB")
        results = fashion_lab_service.image_search_from_pil(img, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot decode image: {exc}")
    return {
        "filename": file.filename,
        "modality": "image -> image_embedding",
        "results":  results,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5 - Cross-modal search
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/search/cross/text-to-image",
            summary="[Phase 5] Cross-modal: text query -> image results")
def text_to_image(
    query: str = Query(..., description="Text query, e.g. 'red running shoes'"),
    top_k: int = Query(TOP_K_DEFAULT, ge=1, le=20),
):
    """
    CONCEPT: Cross-modal retrieval - CLIP shared embedding space.

    A TEXT query is encoded and searched against IMAGE embeddings.
    This finds products whose PHOTOS visually match the text description,
    even if no product name contains those exact words.

    KEY INSIGHT: CLIP projects text and images into the SAME 512-dim space.
    'red shoes' as text and a photo of red shoes are close to each other.

    Compare this result with /search/text?query=... to see the difference.
    """
    results = fashion_lab_service.text_to_image_search(query, top_k)
    return {
        "query":    query,
        "modality": "text -> image_embedding  (cross-modal)",
        "concept":  "Finds products whose PHOTOS match the text description",
        "results":  results,
    }


@router.post("/search/cross/image-to-text",
             summary="[Phase 5] Cross-modal: image query -> text results")
def image_to_text(body: ImageSearchRequest):
    """
    CONCEPT: Reverse cross-modal - image query searches TEXT embeddings.

    An IMAGE is encoded and searched against TEXT embeddings.
    This finds products whose NAMES semantically describe what the image shows,
    even if those products do not visually resemble the query image.

    KEY INSIGHT: Because CLIP aligns modalities, a photo of a shoe
    will have a similar vector to the text 'leather sports shoe'.
    """
    try:
        results = fashion_lab_service.image_to_text_search(body.url, body.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "image_url": body.url,
        "modality":  "image -> text_embedding  (cross-modal)",
        "concept":   "Finds products whose NAMES describe the image content",
        "results":   results,
    }


@router.post("/search/cross/image-to-text/by-upload",
             summary="[Phase 5] Cross-modal: image upload -> text results")
async def image_to_text_upload(
    file:  UploadFile,
    top_k: int = Query(TOP_K_DEFAULT, ge=1, le=20),
):
    """Same as /search/cross/image-to-text but accepts a local file instead of a URL."""
    try:
        contents = await file.read()
        img = PILImage.open(io.BytesIO(contents)).convert("RGB")
        results = fashion_lab_service.image_to_text_search_from_pil(img, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot decode image: {exc}")
    return {
        "filename": file.filename,
        "modality": "image -> text_embedding  (cross-modal)",
        "concept":  "Finds products whose NAMES describe the image content",
        "results":  results,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 6 - Multimodal fusion
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/search/multimodal",
             summary="[Phase 6] Multimodal: weighted fusion of text + image")
def multimodal_search(body: MultimodalRequest):
    """
    CONCEPT: Combining modalities with weighted score fusion.

    Runs TWO searches independently:
      - text_vec  -> text_embedding   (text semantic similarity)
      - image_vec -> image_embedding  (visual similarity)

    Then fuses the ranked lists using weighted Reciprocal Rank Fusion (RRF):
      fused_score(d) = text_weight  * 1/(rank_text(d)  + 60)
                     + image_weight * 1/(rank_image(d) + 60)

    text_weight=1.0 -> pure text search
    text_weight=0.0 -> pure image search
    text_weight=0.5 -> equal mix (default)
    """
    try:
        results = fashion_lab_service.multimodal_search(
            body.text, body.image_url, body.text_weight, body.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    iw = round(1.0 - body.text_weight, 2)
    return {
        "text":         body.text,
        "image_url":    body.image_url,
        "text_weight":  body.text_weight,
        "image_weight": iw,
        "modality":     "text + image -> RRF fusion",
        "results":      results,
    }


@router.post("/search/multimodal/by-upload",
             summary="[Phase 6] Multimodal: text + image fusion (file upload)")
async def multimodal_search_upload(
    file:         UploadFile,
    text:         str   = Form(...),
    text_weight:  float = Form(0.5),
    top_k:        int   = Form(TOP_K_DEFAULT),
):
    """
    Same as /search/multimodal but accepts a local file instead of a URL.
    Other parameters (text, text_weight, top_k) are sent as form fields.
    """
    if not 0.0 <= text_weight <= 1.0:
        raise HTTPException(status_code=400, detail="text_weight must be between 0.0 and 1.0")
    if not 1 <= top_k <= 20:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 20")
    try:
        contents = await file.read()
        img = PILImage.open(io.BytesIO(contents)).convert("RGB")
        results = fashion_lab_service.multimodal_search_from_pil(text, img, text_weight, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot decode image: {exc}")

    iw = round(1.0 - text_weight, 2)
    return {
        "text":         text,
        "filename":     file.filename,
        "text_weight":  text_weight,
        "image_weight": iw,
        "modality":     "text + image -> RRF fusion",
        "results":      results,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 7 - Advanced scalar operations
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/products/by-year-range", summary="[Phase 7] Range query by year")
def products_by_year_range(
    min_year: int = Query(2010, description="Minimum year (inclusive)"),
    max_year: int = Query(2020, description="Maximum year (inclusive)"),
    limit:    int = Query(20, ge=1, le=100),
):
    """
    CONCEPT: Range operator on numeric fields.

    Milvus supports >=, <=, >, < on INT32/INT64 fields with an INVERTED index.
    Filter: year >= min_year && year <= max_year

    Try: min_year=2012 max_year=2014 - observe that only products from that
    period are returned.
    """
    try:
        rows = fashion_lab_service.products_by_year_range(min_year, max_year, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"min_year": min_year, "max_year": max_year, "count": len(rows), "results": rows}


@router.get("/products/search-by-name-pattern", summary="[Phase 7] LIKE search by name")
def search_by_name_pattern(
    pattern: str = Query(..., description="Text to find in the product name, e.g. 'Shirt'"),
    limit:   int = Query(20, ge=1, le=100),
):
    """
    CONCEPT: LIKE operator for pattern matching on a VARCHAR field.

    Milvus LIKE supports % as a wildcard (same as SQL LIKE).
    Filter: product_name like "%pattern%"

    Difference from semantic search:
      - LIKE: finds an exact substring in the string (lexical matching)
      - /search/text: semantic similarity (understands synonyms and context)

    Try: 'Shirt' vs /search/text?query=shirt - observe the difference in results.
    """
    try:
        rows = fashion_lab_service.products_by_name_pattern(pattern, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"pattern": pattern, "count": len(rows), "results": rows}


@router.get("/products/missing-images", summary="[Phase 7] Products without a photo (has_image == false)")
def products_without_images(limit: int = Query(20, ge=1, le=100)):
    """
    CONCEPT: Boolean field filtering - has_image == false.

    These products have image_embedding = zero vector.
    Visual similarity for them is unreliable - useful for data validation.

    Try: observe that these are mostly older or rare items for which
    photos were not available in the source dataset.
    """
    rows = fashion_lab_service.products_without_images(limit)
    return {"has_image": False, "count": len(rows), "results": rows}


@router.get("/products/multi-color", summary="[Phase 7] IN operator - multiple colours at once")
def products_in_colors(
    colors: str = Query(..., description="Comma-separated list of colours, e.g. 'Blue,Red,Black'"),
    limit:  int = Query(20, ge=1, le=100),
):
    """
    CONCEPT: IN operator for filtering on a set of values.

    Filter: base_colour in ["Blue", "Red", "Black"]
    Equivalent SQL: WHERE base_colour IN ('Blue', 'Red', 'Black')

    More efficient than multiple OR conditions - Milvus optimizes IN over INVERTED indexes.
    Try: 'Blue,Black,White' - typical neutral colours.
    """
    color_list = [c.strip() for c in colors.split(",") if c.strip()]
    try:
        rows = fashion_lab_service.products_in_colors(color_list, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"colors": color_list, "count": len(rows), "results": rows}


@router.get("/products/paginated", summary="[Phase 7] Paginated results (offset pagination)")
def paginated_products(
    gender:    Optional[str] = Query(None, description="Gender filter (optional)"),
    page:      int           = Query(1,    ge=1,  description="Page number"),
    page_size: int           = Query(10,   ge=1, le=100, description="Page size"),
):
    """
    CONCEPT: Offset-based pagination for iterating through a large result set.

    Milvus query() supports the offset parameter (limit/offset pagination).
    For larger collections (millions of rows) query_iterator() is preferred -
    it pages results directly without reading the entire set into memory.

    In this demo (1 000 rows) the offset method is perfectly efficient.
    Milvus guarantees that offset + limit cannot exceed 16 384 by default.

    Try: gender='Men', page=1 vs page=2 vs page=3 - observe different records.
    """
    filter_expr = f'gender == "{gender}"' if gender else ""
    try:
        result = fashion_lab_service.paginated_products(filter_expr, page, page_size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@router.get("/products/random-sample", summary="[Phase 7] Random data sample")
def random_sample(
    sample_size: int = Query(10, ge=1, le=100, description="Number of random records"),
):
    """
    CONCEPT: Random sampling for data exploration and validation.

    Useful for:
      - Quick overview of what is in the collection
      - Validating that ingestion correctly wrote diverse categories
      - Generating test examples for search

    Implementation: Python random.sample over all 1 000 rows.
    In production: Milvus 2.6 supports a RANDOM_SAMPLE(rate) filter expression.
    """
    try:
        rows = fashion_lab_service.get_random_sample(sample_size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"sample_size": sample_size, "results": rows}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 7b - Advanced search with complex filters
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/search/advanced-filter", summary="[Phase 7b] ANN search with complex boolean filter")
def advanced_filtered_search(
    query:        str            = Query(..., description="Text query"),
    genders:      Optional[str] = Query(None, description="Comma-separated: Women,Men,Boys,Girls"),
    seasons:      Optional[str] = Query(None, description="Comma-separated: Summer,Winter,Spring,Fall"),
    colours:      Optional[str] = Query(None, description="Comma-separated: Blue,Red,Black"),
    min_year:     Optional[int] = Query(None, description="Minimum year"),
    exclude_type: Optional[str] = Query(None, description="article_type to exclude"),
    top_k:        int            = Query(TOP_K_DEFAULT, ge=1, le=20),
):
    """
    CONCEPT: Combining AND/IN/>=/ != operators in a single filter expression.

    The built filter expression (visible in the response) demonstrates how Milvus
    combines scalar pre-filtering with ANN search:
      gender in [...]  AND  season in [...]  AND  year >= N  AND  article_type != "..."

    Milvus applies the scalar filter FIRST (using INVERTED indexes),
    then runs ANN only over the filtered subset - more efficient than
    post-filtering.

    Try: query='casual shirt', genders='Women', seasons='Summer,Spring', min_year=2012
    """
    gender_list  = [g.strip() for g in genders.split(",") if g.strip()]  if genders  else None
    season_list  = [s.strip() for s in seasons.split(",") if s.strip()]  if seasons  else None
    colour_list  = [c.strip() for c in colours.split(",") if c.strip()]  if colours  else None
    try:
        result = fashion_lab_service.advanced_filtered_search(
            query, gender_list, season_list, colour_list, min_year, exclude_type, top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "query":       query,
        "filter_expr": result["filter_expr"],
        "modality":    "text -> text_embedding (complex pre-filter)",
        "results":     result["results"],
    }


@router.get("/search/by-threshold", summary="[Phase 7b] Search with minimum score threshold")
def search_by_threshold(
    query:     str   = Query(..., description="Text query"),
    min_score: float = Query(0.7, ge=0.0, le=1.0, description="Minimum COSINE score (0.0-1.0)"),
    top_k:     int   = Query(TOP_K_DEFAULT, ge=1, le=20),
):
    """
    CONCEPT: Post-filtering by score threshold - returns only relevant results.

    COSINE similarity: 1.0 = identical, 0.0 = completely different.
    Typical thresholds:
      >= 0.9 -> near-identical products
      >= 0.7 -> highly relevant (recommended)
      >= 0.5 -> moderately relevant

    Implementation: fetches 10x more candidates than top_k, then discards
    those with score < min_score. Returns an empty list if none pass the threshold.

    Try: min_score=0.9 vs 0.7 vs 0.5 - observe how the result count changes.
    """
    try:
        results = fashion_lab_service.search_by_threshold(query, min_score, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "query":     query,
        "min_score": min_score,
        "count":     len(results),
        "modality":  "text -> text_embedding (score threshold post-filter)",
        "results":   results,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8 - Analytics
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/analytics/count-by-category", summary="[Phase 8] COUNT(*) aggregation by category")
def count_by_category(
    category: str = Query(..., description="master_category value, e.g. 'Apparel'"),
):
    """
    CONCEPT: COUNT(*) aggregation - Milvus query with output_fields=['count(*)'].

    Equivalent SQL: SELECT COUNT(*) FROM fashion_lab WHERE master_category = '...'

    Difference from scalar search:
      - query() with output_fields=['count(*)'] returns only the count, no data
      - Faster and more memory-efficient than fetching all rows and counting in code

    Try: 'Apparel', 'Footwear', 'Accessories' - observe the data distribution.
    """
    try:
        return fashion_lab_service.count_by_category(category)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/analytics/facets", summary="[Phase 8] Faceted search - counts per categorical field")
def get_facets():
    """
    CONCEPT: Faceted aggregation - foundation for UI filters in e-commerce apps.

    Returns occurrence counts for each value across fields:
      gender, master_category, base_colour, season, article_type

    E.g. {'gender': {'Men': 540, 'Women': 360, ...}, 'season': {'Summer': 280, ...}}

    In SQL systems: GROUP BY + COUNT per column.
    Milvus implementation: query() -> Python Counter (no native GROUP BY).

    Try: use these values as valid filter values in /products and /search/filtered endpoints.
    """
    try:
        return fashion_lab_service.get_facets()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# Phase 9 - Advanced searches (search parameters and strategies)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/search/paginated", summary="[Phase 9] ANN search with result pagination")
def search_paginated(
    query:     str = Query(..., description="Text query"),
    page:      int = Query(1,  ge=1,  description="Page number (starts at 1)"),
    page_size: int = Query(10, ge=1, le=50, description="Results per page"),
):
    """
    CONCEPT: Offset-based pagination of vector search results.

    Milvus search() supports the offset parameter which skips the first N results.
    Limit: offset + limit < 16 384 (Milvus maximum).

    Difference from /products/paginated:
      - /products/paginated - scalar search (no similarity ranking)
      - /search/paginated   - ANN search (ranked by COSINE similarity)

    Try: same query on page=1, 2, 3 - observe the continuation of the ranked list.
    """
    try:
        return fashion_lab_service.search_paginated(query, page, page_size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/search/iterator", summary="[Phase 9] Iterator search - iterate through all results")
def search_with_iterator(
    query:      str = Query(..., description="Text query"),
    batch_size: int = Query(50, ge=5, le=100, description="Batch size per iteration"),
):
    """
    CONCEPT: Search iterator - exhaustive search through all results in batches.

    Instead of a single call for all results, the iterator returns them in batches.
    Useful when the total number of results is unknown or large.

    API equivalent: Collection.search_iterator() (ORM API) or
    successive client.search() calls with increasing offset values.

    Implementation here: offset iteration until no more results.
    Traverses all 1 000 rows of the collection.

    Try: batch_size=10 vs batch_size=100 - same results, different number of batches.
    """
    try:
        return fashion_lab_service.search_with_iterator(query, batch_size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/search/grouped", summary="[Phase 9] Grouped search - diverse results per field")
def grouped_search(
    query:          str = Query(..., description="Text query"),
    group_by_field: str = Query("article_type", description="Field to group by: gender | master_category | article_type | base_colour | season"),
    group_size:     int = Query(1, ge=1, le=3, description="Max results per group"),
    top_k:          int = Query(10, ge=1, le=20),
):
    """
    CONCEPT: Grouping search - guarantees result diversity by category.

    Without grouping, top-k could contain e.g. 10 different variants of the
    same article_type (all shirts). With group_by_field='article_type' and
    group_size=1, each article_type is represented by at most 1 result.

    Useful for:
      - E-commerce: show different clothing types, not just the most similar type
      - Recommendations: diversify results

    Try: query='casual clothes', group_by_field='article_type', group_size=1
    - observe that results come from different article categories.
    """
    try:
        results = fashion_lab_service.grouped_search(query, group_by_field, group_size, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "query":          query,
        "group_by_field": group_by_field,
        "group_size":     group_size,
        "modality":       "text -> text_embedding (grouped)",
        "results":        results,
    }


@router.get("/search/range", summary="[Phase 9] Range search - COSINE score range")
def range_search(
    query:     str   = Query(..., description="Text query"),
    min_score: float = Query(0.5, ge=0.0, le=1.0, description="Minimum COSINE score (inclusive)"),
    max_score: float = Query(1.0, ge=0.0, le=1.0, description="Maximum COSINE score (inclusive)"),
):
    """
    CONCEPT: Native Milvus range search - score filter inside Milvus.

    Difference from /search/by-threshold (Python post-filter):
      - /search/by-threshold: fetches N candidates -> filter in Python
      - /search/range: Milvus IVF_FLAT does not return results outside the range at all
        (more efficient, no bandwidth wasted on discarded results)

    Parameters (COSINE metric - higher score = more similar):
      min_score=0.5, max_score=1.0 -> anything with at least 50% similarity
      min_score=0.8, max_score=0.95 -> highly similar but not duplicates
      min_score=0.0, max_score=0.5 -> only unrelated results (for demonstration)

    Try: min_score=0.7 max_score=0.9 - observe that no results fall below/above the range.
    """
    try:
        results = fashion_lab_service.range_search(query, min_score, max_score)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "query":     query,
        "min_score": min_score,
        "max_score": max_score,
        "count":     len(results),
        "modality":  "text -> text_embedding (native range search)",
        "results":   results,
    }


@router.get("/search/consistency", summary="[Phase 9] Search consistency - Strong vs Eventually")
def search_with_consistency(
    query:             str = Query(..., description="Text query"),
    consistency_level: str = Query("Eventually", description="Strong | Session | Bounded | Eventually"),
    top_k:             int = Query(TOP_K_DEFAULT, ge=1, le=20),
):
    """
    CONCEPT: Read consistency - trade-off between latency and accuracy.

    Milvus supports 4 consistency levels (similar to Cassandra tunable consistency):

      Strong      -> always reads the latest data (waits for all nodes to synchronize)
                   -> lowest latency variance, but highest latency
      Bounded     -> reads data no older than a specified interval
      Session     -> same client always sees its own writes (default)
      Eventually  -> reads available data without waiting (fastest, may see stale data)

    For the lab (1 node, ~1000 rows) speed differences are not measurable,
    but the concept is critical for distributed systems.

    Try: same query with Strong vs Eventually - results should be identical
    for a static collection, but latency may vary in production.
    """
    try:
        results = fashion_lab_service.search_with_consistency(query, consistency_level, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "query":             query,
        "consistency_level": consistency_level,
        "modality":          "text -> text_embedding",
        "results":           results,
    }


@router.get("/search/hybrid/weighted", summary="[Phase 9] Hybrid search - WeightedRanker (vs RRFRanker)")
def hybrid_search_weighted(
    query:       str   = Query(..., description="Text query"),
    text_weight: float = Query(0.7, ge=0.0, le=1.0, description="Weight for text_embedding (image = 1 - text)"),
    top_k:       int   = Query(TOP_K_DEFAULT, ge=1, le=20),
):
    """
    CONCEPT: WeightedRanker - alternative to RRFRanker in hybrid_search.

    Difference between rankers:
      RRFRanker (/search/hybrid):
        - Works with ranks, not scores
        - More robust for fields with different score scales
        - formula: score = sum(weight_i / (rank_i + k))

      WeightedRanker (this endpoint):
        - Directly combines normalized score values
        - formula: score = text_weight * score_text + image_weight * score_image
        - Better when score scales are compatible (both COSINE -> both in [0,1])

    For the CLIP model (both fields COSINE, same space) WeightedRanker is more intuitive.

    Try: text_weight=0.9 (text dominant) vs 0.1 (image dominant) -
    observe the ordering difference compared to /search/hybrid (RRF).
    """
    try:
        results = fashion_lab_service.hybrid_search_weighted(query, text_weight, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    iw = round(1.0 - text_weight, 4)
    return {
        "query":        query,
        "text_weight":  text_weight,
        "image_weight": iw,
        "ranker":       "WeightedRanker",
        "modality":     "text -> [text_embedding * w + image_embedding * (1-w)]",
        "results":      results,
    }


@router.post("/search/batch", summary="[Phase 9] Batch search - multiple queries in a single call")
def batch_search(body: BatchSearchRequest):
    """
    CONCEPT: Batch vector search - N queries in a single Milvus search() call.

    Milvus search() accepts data as a list of vectors - all queries are processed
    in parallel inside Milvus in a single round-trip.

    More efficient than N separate /search/text calls because:
      - One network round-trip (instead of N)
      - Milvus can batch internally at the GPU/SIMD level
      - CLIP model encodes all texts in a single batch call

    Limit: max 10 queries per request in this demo.

    Try: ['blue jeans', 'red dress', 'white shoes'] - 3 searches at once.
    """
    try:
        results = fashion_lab_service.batch_text_search(body.queries, body.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"query_count": len(body.queries), "top_k": body.top_k, "results": results}


@router.get("/search/template-filter", summary="[Phase 9] Filter templating - parameterized filters")
def search_template_filter(
    query:    str = Query(..., description="Text query"),
    min_year: int = Query(2012, description="Minimum year (template parameter)"),
    colors:   str = Query("Blue,Black,White", description="Comma-separated list of colours"),
    top_k:    int = Query(TOP_K_DEFAULT, ge=1, le=20),
):
    """
    CONCEPT: Parameterized filter expressions for reusable filtering logic.

    The filter template approach separates filter structure from parameter values.
    Analogous to PreparedStatement in SQL - the structure is compiled once,
    values change without reconstructing the string.

    Template: 'year >= {min_year} && base_colour in [{colors}]'
    Parameters: min_year=2012, colors=["Blue", "Black", "White"]

    Advantages:
      - Safe from injection attacks (parameters are sanitized separately)
      - Milvus 2.6 natively supports filter_params for template optimization
      - Cleaner code - logic and data are separated

    Try: change min_year and colors without changing the filter structure.
    """
    color_list = [c.strip() for c in colors.split(",") if c.strip()]
    try:
        result = fashion_lab_service.search_template_filter(query, min_year, color_list, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "query":       query,
        "filter_expr": result["filter_expr"],
        "modality":    "text -> text_embedding (template filter)",
        "results":     result["results"],
    }


@router.get("/search/partition", summary="[Phase 9] Search within a partition")
def search_in_partition(
    query:     str = Query(..., description="Text query"),
    partition: str = Query("_default", description="Partition name (default: _default)"),
    top_k:     int = Query(TOP_K_DEFAULT, ge=1, le=20),
):
    """
    CONCEPT: Partition-based search - search restricted to a data subset.

    Milvus partitions are logical divisions of a collection (like sharding within a single node).
    Searching within a partition skips the others - faster for collections with millions of rows.

    In this demo there is only the '_default' partition.
    In a production system you would create partitions by e.g. gender:
      client.create_partition("fashion_lab", "Men")
      client.create_partition("fashion_lab", "Women")
    and specify the target partition at insert time.

    Then searching in the 'Men' partition would skip ~60% of data (Women, Kids).

    Try with partition='_default' to see how the partition is specified in the API.
    """
    try:
        result = fashion_lab_service.search_in_partition(query, partition, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "query":     query,
        "partition": result["partition"],
        "modality":  "text -> text_embedding (partition search)",
        "results":   result["results"],
    }


@router.get("/stats", summary="Collection statistics")
def lab_stats():
    """Row count and basic information about the fashion_lab collection."""
    try:
        stats = fashion_lab_service.get_stats()
        return {"collection": "fashion_lab", "row_count": stats.get("row_count", 0)}
    except Exception as exc:
        return {"error": str(exc), "hint": "Run ingestion first: python -m ingest.fashion_lab_ingest"}
