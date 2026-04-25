import logging

from fastapi import APIRouter, HTTPException, Query

from config import BOOK_REVIEWS_COLLECTION, REVIEWS_DEFAULT_TOP_K
from model.book_review import BookReviewCreate, BookReviewUpdate
from schema.reviews_schema import reviews_schema, reviews_index_params
from service.impl.reviews_service import reviews_service
from services.milvus_service import milvus_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/reviews", tags=["Book Reviews"])


# ── Phase 0: Schema management ───────────────────────────────────────────────

@router.post("/schema/reset", summary="Drop and recreate the book_reviews collection")
def reset_schema():
    client = milvus_service.client
    if client.has_collection(BOOK_REVIEWS_COLLECTION):
        client.drop_collection(BOOK_REVIEWS_COLLECTION)
    client.create_collection(
        collection_name=BOOK_REVIEWS_COLLECTION,
        schema=reviews_schema(client),
        index_params=reviews_index_params(client),
        consistency_level="Strong",
    )
    milvus_service.load_collection(BOOK_REVIEWS_COLLECTION)
    return {"status": "recreated", "collection": BOOK_REVIEWS_COLLECTION}


@router.get("/stats", summary="Collection row count and name")
def get_stats():
    try:
        return reviews_service.get_stats()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/health", summary="Milvus connectivity check for this collection")
def health_check():
    healthy = _reviews_repository_health()
    return {"healthy": healthy, "collection": BOOK_REVIEWS_COLLECTION}


def _reviews_repository_health() -> bool:
    from repository.reviews_repository import reviews_repository
    return reviews_repository.health_check()


# ── Phase 1: CRUD ─────────────────────────────────────────────────────────────

@router.post("/", summary="Insert a single book review")
def create_review(review: BookReviewCreate):
    try:
        return reviews_service.create_review(review)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/batch", summary="Insert up to 400 reviews in one call")
def batch_create(reviews: list[BookReviewCreate]):
    try:
        return reviews_service.batch_create(reviews)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/by-review-id/{review_business_id}", summary="Get review by business review_id (string key)")
def get_review_by_business_id(review_business_id: str):
    try:
        return reviews_service.get_review_by_business_id(review_business_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{review_id}", summary="Get review by Milvus ID")
def get_review(review_id: int):
    try:
        return reviews_service.get_review(review_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/", summary="List reviews with optional filters")
def list_reviews(
    isbn:       str | None = Query(default=None),
    min_rating: int | None = Query(default=None, ge=1, le=5),
    max_rating: int | None = Query(default=None, ge=1, le=5),
    user_type:  str | None = Query(default=None),
    limit:      int        = Query(default=20, ge=1, le=200),
    offset:     int        = Query(default=0, ge=0),
):
    try:
        return reviews_service.list_reviews(isbn, min_rating, max_rating, user_type, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/{review_id}", summary="Update review by Milvus ID (partial update)")
def update_review(review_id: int, update: BookReviewUpdate):
    try:
        return reviews_service.update_review(review_id, update)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{review_id}", summary="Delete review by Milvus ID")
def delete_review(review_id: int):
    try:
        return reviews_service.delete_review(review_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Phase 2: Search ───────────────────────────────────────────────────────────

@router.get(
    "/search/semantic",
    summary="Dense ANN — MiniLM encodes query → cosine search on review_embedding",
    description=(
        "Optionally pre-filter results by isbn, min_rating, and/or user_type "
        "before running ANN to narrow the candidate set."
    ),
)
def semantic_search(
    query:      str        = Query(..., min_length=1),
    top_k:      int        = Query(default=REVIEWS_DEFAULT_TOP_K, ge=1, le=50),
    isbn:       str | None = Query(default=None, description="Filter to reviews for a specific ISBN"),
    min_rating: int | None = Query(default=None, ge=1, le=5, description="Minimum star rating"),
    user_type:  str | None = Query(default=None, description="Filter by reviewer type"),
):
    try:
        return reviews_service.semantic_search(query, top_k, isbn, min_rating, user_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/search/tuning",
    summary="Dense ANN with custom nprobe — demonstrates IVF_FLAT precision/speed trade-off",
    description=(
        "nprobe controls how many IVF clusters are scanned. "
        "Higher nprobe → more accurate but slower. "
        f"Default top_k is {REVIEWS_DEFAULT_TOP_K}. "
        "Compare results against /search/semantic to see the effect."
    ),
)
def search_with_nprobe(
    query:      str        = Query(..., min_length=1),
    nprobe:     int        = Query(..., ge=1, le=64, description="Number of IVF clusters to probe"),
    top_k:      int        = Query(default=REVIEWS_DEFAULT_TOP_K, ge=1, le=50),
    isbn:       str | None = Query(default=None),
    min_rating: int | None = Query(default=None, ge=1, le=5),
    user_type:  str | None = Query(default=None),
):
    try:
        return reviews_service.search_with_nprobe(query, nprobe, top_k, isbn, min_rating, user_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
