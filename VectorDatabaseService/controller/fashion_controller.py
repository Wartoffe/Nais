"""
Controller for operations on the fashion_products collection.
Route prefix: /api/v1/fashion

Phase 0 - Collection management
  POST /schema/reset              Drop and recreate the collection (destructive demo reset)
  GET  /stats                     Row count and collection info

Phase 1 - CRUD
  POST   /products                Insert a single product (text + image URL)
  GET    /products/{id}           Fetch by Milvus ID
  GET    /products/{id}/vectors   Fetch with raw embeddings
  GET    /products                Scalar-filtered listing (paginated)
  PUT    /products/{id}           Update (re-encodes changed attributes)
  DELETE /products/{id}           Delete by ID

Phase 2 - Text queries
  GET  /search/text/semantic       Free text -> finds similar product names
  GET  /search/text/filtered       Free text + scalar pre-filter
  GET  /search/text/facet-colour   Text query restricted to a single colour

Phase 3 - Image queries
  POST /search/image/by-upload     Upload image -> visual similarity search
  POST /search/image/by-url        Image URL -> visual similarity search
  POST /search/image/by-base64     Base64 image -> visual similarity search

Phase 4 - Cross-modal queries
  GET  /search/cross/text-to-image  Text query -> searches image_embedding
  POST /search/cross/image-to-text  Image     -> searches text_embedding

Phase 5 - Advanced / complex queries
  GET  /search/advanced/similar/{id}    Finds similar products using both embeddings + RRF
  POST /search/advanced/two-stage       Image ANN recall -> text cosine reranking
  POST /search/advanced/multimodal      Text + image; weighted RRF fusion
  GET  /search/advanced/batch-text      Multiple text queries in a single round-trip
  GET  /search/advanced/year-range      Scalar filter on year range
  POST /search/advanced/filtered-image  Image upload + scalar filter
"""

import logging

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from config import DEFAULT_TOP_K, FASHION_COLLECTION, TWO_STAGE_RECALL
from model.fashion_product import (
    FashionProductCreate,
    FashionProductUpdate,
    MultimodalRequest,
    TwoStageRequest,
)
from service.impl.fashion_service import fashion_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/fashion", tags=["Fashion - Multimodal"])


def _build_filter(**kwargs) -> str:
    """Builds a Milvus boolean expression from HTTP query parameters (None values are ignored)."""
    clauses = []
    if kwargs.get("gender"):          clauses.append(f'gender == "{kwargs["gender"]}"')
    if kwargs.get("master_category"): clauses.append(f'master_category == "{kwargs["master_category"]}"')
    if kwargs.get("article_type"):    clauses.append(f'article_type == "{kwargs["article_type"]}"')
    if kwargs.get("base_colour"):     clauses.append(f'base_colour == "{kwargs["base_colour"]}"')
    if kwargs.get("season"):          clauses.append(f'season == "{kwargs["season"]}"')
    if kwargs.get("usage"):           clauses.append(f'usage == "{kwargs["usage"]}"')
    return " && ".join(clauses)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 0 - Collection management
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/schema/reset",
    summary="[Phase 0] Drop and recreate the collection (destructive demo reset)",
    tags=["Phase 0 - Collection Management"],
)
def reset_schema():
    """Drops and recreates the fashion_products collection with all indexes."""
    fashion_service.reset_collection()
    return {"message": f"Collection '{FASHION_COLLECTION}' has been reset."}


@router.get(
    "/stats",
    summary="[Phase 0] Collection statistics",
    tags=["Phase 0 - Collection Management"],
)
def collection_stats():
    return fashion_service.get_stats()


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 - CRUD
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/products",
    summary="[Phase 1] Insert a single product (text + optional image)",
    tags=["Phase 1 - CRUD"],
)
def create_product(product: FashionProductCreate):
    """
    Encodes the product name as text_embedding (CLIP text tower).
    If image_url is provided, also encodes it as image_embedding (CLIP image tower).
    Otherwise image_embedding is a zero vector and has_image is False.
    """
    try:
        return fashion_service.create_product(product)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/products/{product_id}",
    summary="[Phase 1] Fetch product by Milvus ID",
    tags=["Phase 1 - CRUD"],
)
def get_product(product_id: int):
    try:
        return fashion_service.get_product(product_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.get(
    "/products/{product_id}/vectors",
    summary="[Phase 1] Fetch product with raw embeddings",
    tags=["Phase 1 - CRUD"],
)
def get_product_with_vectors(product_id: int):
    """Returns the stored text_embedding and image_embedding (512-dim each)."""
    try:
        return fashion_service.get_product_with_vectors(product_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Product not found")


@router.get(
    "/products",
    summary="[Phase 1] Scalar-filtered listing (no vector ranking)",
    tags=["Phase 1 - CRUD"],
)
def list_products(
    gender:          str | None  = Query(None, description="e.g. Men, Women, Boys, Girls, Unisex"),
    master_category: str | None  = Query(None, description="e.g. Apparel, Footwear, Accessories"),
    article_type:    str | None  = Query(None, description="e.g. Tshirts, Jeans, Casual Shoes"),
    base_colour:     str | None  = Query(None, description="e.g. Navy Blue, Black, White"),
    season:          str | None  = Query(None, description="e.g. Summer, Winter, Fall, Spring"),
    year:            int | None  = Query(None),
    usage:           str | None  = Query(None, description="e.g. Casual, Formal, Sports"),
    has_image:       bool | None = Query(None, description="Filter to items that have images"),
    limit:           int         = Query(20, ge=1, le=200),
    offset:          int         = Query(0, ge=0),
):
    """Pure scalar filter - no ANN search. Demonstrates Milvus WHERE expressions."""
    products = fashion_service.list_products(
        gender, master_category, article_type, base_colour,
        season, year, usage, has_image, limit, offset,
    )
    return {"count": len(products), "results": [p.model_dump() for p in products]}


@router.put(
    "/products/{product_id}",
    summary="[Phase 1] Update product (upsert - re-encodes if text or image changes)",
    tags=["Phase 1 - CRUD"],
)
def update_product(product_id: int, update: FashionProductUpdate):
    """
    Milvus has no partial in-place update - we fetch, merge, then upsert.
    Embeddings are regenerated when product_name or image_url changes.
    """
    try:
        return fashion_service.update_product(product_id, update)
    except KeyError:
        raise HTTPException(status_code=404, detail="Product not found")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.delete(
    "/products/{product_id}",
    summary="[Phase 1] Delete product by Milvus ID",
    tags=["Phase 1 - CRUD"],
)
def delete_product(product_id: int):
    return fashion_service.delete_product(product_id)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 - Text queries
#   Query vector = CLIP text encoding  ->  searches text_embedding
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/search/text/semantic",
    summary="[Phase 2] Text -> semantic text search",
    tags=["Phase 2 - Text Queries"],
)
def text_semantic_search(
    query: str = Query(..., description="Free text, e.g. 'blue slim fit jeans'"),
    top_k: int = Query(DEFAULT_TOP_K, ge=1, le=100),
):
    """
    Encodes the text query with the CLIP text tower, then searches text_embedding.
    Finds products whose names are semantically similar to the query.
    """
    results = fashion_service.text_search(query, top_k)
    return {"query": query, "results": [r.model_dump() for r in results]}


@router.get(
    "/search/text/filtered",
    summary="[Phase 2] Semantic text search + scalar pre-filter",
    tags=["Phase 2 - Text Queries"],
)
def text_filtered_search(
    query:           str      = Query(...),
    gender:          str | None = Query(None),
    master_category: str | None = Query(None),
    article_type:    str | None = Query(None),
    season:          str | None = Query(None),
    base_colour:     str | None = Query(None),
    usage:           str | None = Query(None),
    top_k:           int      = Query(DEFAULT_TOP_K, ge=1, le=100),
):
    """
    ANN search with pre-filter: Milvus applies the WHERE clause BEFORE the ANN search -
    only products satisfying the filter are candidates for vector search.
    """
    filter_expr = _build_filter(
        gender=gender, master_category=master_category, article_type=article_type,
        season=season, base_colour=base_colour, usage=usage,
    )
    results = fashion_service.filtered_text_search(query, filter_expr, top_k)
    return {"query": query, "filter": filter_expr, "results": [r.model_dump() for r in results]}


@router.get(
    "/search/text/facet-colour",
    summary="[Phase 2] Text query restricted to a single colour",
    tags=["Phase 2 - Text Queries"],
)
def text_colour_facet(
    query:       str = Query(..., description="e.g. 'casual summer wear'"),
    base_colour: str = Query(..., description="e.g. 'Navy Blue'"),
    top_k:       int = Query(DEFAULT_TOP_K, ge=1, le=100),
):
    """ANN text search restricted to products of a specific colour - simulates faceted search."""
    results = fashion_service.colour_facet_search(query, base_colour, top_k)
    return {"query": query, "colour_filter": base_colour, "results": [r.model_dump() for r in results]}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 - Image queries
#   Query vector = CLIP image encoding  ->  searches image_embedding
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/search/image/by-upload",
    summary="[Phase 3] Upload image -> visual similarity search",
    tags=["Phase 3 - Image Queries"],
)
async def image_search_by_upload(
    file:        UploadFile = File(..., description="Product photo (JPG/PNG/WebP)"),
    top_k:       int  = Form(DEFAULT_TOP_K),
    images_only: bool = Form(False, description="Restrict results to items that have images"),
):
    """
    Uploads a product photo. The image is encoded with the CLIP vision tower and
    used as the query vector to search image_embedding.
    Testable in Swagger UI: click 'Try it out', select a file, click Execute.
    """
    data = await file.read()
    try:
        results = fashion_service.image_search_by_bytes(data, top_k, images_only)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"results": [r.model_dump() for r in results]}


@router.post(
    "/search/image/by-url",
    summary="[Phase 3] Image URL -> visual similarity search",
    tags=["Phase 3 - Image Queries"],
)
def image_search_by_url(
    image_url:   str  = Query(..., description="Public URL of the product photo"),
    top_k:       int  = Query(DEFAULT_TOP_K, ge=1, le=100),
    images_only: bool = Query(False),
):
    """
    Downloads the image from the given URL, encodes it with CLIP, searches image_embedding.
    Easiest to test directly in Swagger UI.
    """
    try:
        results = fashion_service.image_search_by_url(image_url, top_k, images_only)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"image_url": image_url, "results": [r.model_dump() for r in results]}


@router.post(
    "/search/image/by-base64",
    summary="[Phase 3] Base64 image -> visual similarity search",
    tags=["Phase 3 - Image Queries"],
)
def image_search_by_base64(
    image_base64: str = ...,
    top_k: int = Query(DEFAULT_TOP_K, ge=1, le=100),
):
    """
    Accepts a base64-encoded image (or data-URI) in the request body.
    Useful when calling from a web frontend or an automated test script.
    """
    try:
        results = fashion_service.image_search_by_base64(image_base64, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"results": [r.model_dump() for r in results]}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4 - Cross-modal queries  (CLIP shared embedding space)
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/search/cross/text-to-image",
    summary="[Phase 4] Text -> cross-modal image search",
    tags=["Phase 4 - Cross-Modal"],
)
def text_to_image_search(
    query:       str  = Query(..., description="Text description, e.g. 'red floral summer dress'"),
    top_k:       int  = Query(DEFAULT_TOP_K, ge=1, le=100),
    images_only: bool = Query(True, description="Return only products that have images"),
):
    """
    KEY CONCEPT: text query -> searches image_embedding field.

    Because CLIP text and image towers share the same latent space, text embeddings
    and image embeddings are directly comparable by cosine similarity.
    This returns products whose PHOTOS match the text description.
    """
    results = fashion_service.text_to_image_search(query, top_k, images_only)
    return {
        "query":   query,
        "mode":    "text_query -> image_embedding  (finds products that LOOK like the description)",
        "results": [r.model_dump() for r in results],
    }


@router.post(
    "/search/cross/image-to-text",
    summary="[Phase 4] Image -> cross-modal text search",
    tags=["Phase 4 - Cross-Modal"],
)
async def image_to_text_search(
    file:  UploadFile = File(...),
    top_k: int = Form(DEFAULT_TOP_K),
):
    """
    KEY CONCEPT: image -> searches text_embedding field.

    Encodes the uploaded image with the CLIP image tower, then searches text_embedding.
    Returns products whose NAMES are closest in CLIP space to the uploaded photo.
    """
    data = await file.read()
    try:
        results = fashion_service.image_to_text_search(data, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {
        "mode":    "image_query -> text_embedding  (finds names that describe the image)",
        "results": [r.model_dump() for r in results],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5 - Advanced / complex queries
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/search/advanced/similar/{product_id}",
    summary="[Phase 5] Find similar products using BOTH embeddings (RRF fusion)",
    tags=["Phase 5 - Advanced"],
)
def find_similar_both_fields(
    product_id:  int   = ...,
    top_k:       int   = Query(DEFAULT_TOP_K, ge=1, le=100),
    text_weight: float = Query(0.5, ge=0.0, le=1.0,
                               description="Weight of text similarity vs. visual similarity"),
):
    """
    Two-field similarity search - finds products similar by appearance AND by name.
    Merges two ANN searches using Reciprocal Rank Fusion (RRF).
    """
    try:
        return fashion_service.find_similar(product_id, text_weight, top_k)
    except KeyError:
        raise HTTPException(status_code=404, detail="Product not found")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post(
    "/search/advanced/two-stage",
    summary="[Phase 5] Two-stage: image recall -> text cosine reranking",
    tags=["Phase 5 - Advanced"],
)
def two_stage_search(request: TwoStageRequest):
    """
    Two-stage retrieval pipeline - classic production pattern:
      Stage 1 - image ANN recall (fast, high recall, recall_k candidates)
      Stage 2 - exact text cosine reranking in Python (when text_rerank is provided)
    """
    try:
        return fashion_service.two_stage_search(
            request.image_base64,
            request.text_rerank,
            request.recall_k,
            request.final_k,
            request.filter_expr,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post(
    "/search/advanced/multimodal",
    summary="[Phase 5] Multimodal: weighted fusion of text + image",
    tags=["Phase 5 - Advanced"],
)
def multimodal_fusion_search(request: MultimodalRequest):
    """
    Full multimodal fusion - two ANN searches + RRF merging.
    text_weight controls the balance between text and visual components.
    """
    try:
        results = fashion_service.multimodal_fusion_search(
            request.text_query,
            request.image_base64,
            request.text_weight,
            request.top_k,
            request.filter_expr,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {
        "text_query":   request.text_query,
        "text_weight":  request.text_weight,
        "image_weight": 1 - request.text_weight,
        "results":      [r.model_dump() for r in results],
    }


@router.get(
    "/search/advanced/batch-text",
    summary="[Phase 5] Batch text search - multiple queries in a single round-trip",
    tags=["Phase 5 - Advanced"],
)
def batch_text_search(
    queries: list[str] = Query(..., description="Up to 10 text queries"),
    top_k:   int = Query(5, ge=1, le=50),
):
    """
    Sends multiple text query vectors to Milvus in a single network round-trip.
    Milvus returns independent top-K results for each query vector.
    """
    if len(queries) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 queries per batch request")
    results = fashion_service.batch_text_search(queries, top_k)
    return {"queries": queries, "results": results}


@router.get(
    "/search/advanced/year-range",
    summary="[Phase 5] Text search within a year range",
    tags=["Phase 5 - Advanced"],
)
def year_range_text_search(
    query:     str = Query(...),
    from_year: int = Query(..., description="Start year (inclusive)"),
    to_year:   int = Query(..., description="End year (inclusive)"),
    top_k:     int = Query(DEFAULT_TOP_K, ge=1, le=100),
):
    """Combines ANN text search with a year range filter (year >= X && year <= Y)."""
    results = fashion_service.year_range_search(query, from_year, to_year, top_k)
    return {"query": query, "year_range": [from_year, to_year], "results": [r.model_dump() for r in results]}


@router.post(
    "/search/advanced/filtered-image",
    summary="[Phase 5] Image upload + scalar filter",
    tags=["Phase 5 - Advanced"],
)
async def image_filtered_search(
    file:            UploadFile = File(...),
    gender:          str | None = Form(None),
    master_category: str | None = Form(None),
    article_type:    str | None = Form(None),
    season:          str | None = Form(None),
    top_k:           int = Form(DEFAULT_TOP_K),
):
    """
    Upload an image and restrict results to a specific category/gender/season.
    Demonstrates scalar pre-filtering on an image ANN search.
    """
    data = await file.read()
    filter_expr = _build_filter(
        gender=gender, master_category=master_category,
        article_type=article_type, season=season,
    )
    try:
        results = fashion_service.image_search_by_bytes(
            data, top_k, images_only=False, filter_expr=filter_expr,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"filter": filter_expr, "results": [r.model_dump() for r in results]}
