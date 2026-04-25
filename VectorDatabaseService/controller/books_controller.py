import logging

from fastapi import APIRouter, HTTPException, Query

from config import BOOKS_COLLECTION, BOOKS_DEFAULT_TOP_K
from model.book import BookCreate, BookUpdate
from schema.books_schema import books_schema, books_index_params
from service.impl.books_service import books_service
from services.milvus_service import milvus_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/books", tags=["Books"])


# ── Phase 0: Schema management ───────────────────────────────────────────────

@router.post("/schema/reset", summary="Drop and recreate the books collection")
def reset_schema():
    client = milvus_service.client
    if client.has_collection(BOOKS_COLLECTION):
        client.drop_collection(BOOKS_COLLECTION)
    client.create_collection(
        collection_name=BOOKS_COLLECTION,
        schema=books_schema(client),
        index_params=books_index_params(client),
        consistency_level="Strong",
    )
    milvus_service.load_collection(BOOKS_COLLECTION)
    return {"status": "recreated", "collection": BOOKS_COLLECTION}


@router.get("/stats", summary="Collection row count and name")
def get_stats():
    try:
        return books_service.get_stats()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/health", summary="Milvus connectivity check for this collection")
def health_check():
    healthy = _books_repository_health()
    return {"healthy": healthy, "collection": BOOKS_COLLECTION}


def _books_repository_health() -> bool:
    from repository.books_repository import books_repository
    return books_repository.health_check()


# ── Phase 1: CRUD ─────────────────────────────────────────────────────────────

@router.post("/", summary="Insert a single book")
def create_book(book: BookCreate):
    try:
        return books_service.create_book(book)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/batch", summary="Insert up to 200 books in one call")
def batch_create(books: list[BookCreate]):
    try:
        return books_service.batch_create(books)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/isbn/{isbn}", summary="Get book by ISBN")
def get_book_by_isbn(isbn: str):
    try:
        return books_service.get_book_by_isbn(isbn)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{book_id}", summary="Get book by Milvus ID")
def get_book(book_id: int):
    try:
        return books_service.get_book(book_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/", summary="List books with optional filters")
def list_books(
    genre:     str | None = Query(default=None),
    language:  str | None = Query(default=None),
    year_from: int | None = Query(default=None, ge=0, le=3000),
    year_to:   int | None = Query(default=None, ge=0, le=3000),
    limit:     int        = Query(default=20, ge=1, le=200),
    offset:    int        = Query(default=0, ge=0),
):
    try:
        return books_service.list_books(genre, language, year_from, year_to, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/{book_id}", summary="Update book by Milvus ID (partial update)")
def update_book(book_id: int, update: BookUpdate):
    try:
        return books_service.update_book(book_id, update)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{book_id}", summary="Delete book by Milvus ID")
def delete_book(book_id: int):
    try:
        return books_service.delete_book(book_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Phase 2: Search ───────────────────────────────────────────────────────────

@router.get(
    "/search/semantic",
    summary="Dense ANN — MiniLM encodes query → cosine search on dense_embedding",
)
def semantic_search(
    query: str = Query(..., min_length=1),
    top_k: int = Query(default=BOOKS_DEFAULT_TOP_K, ge=1, le=50),
):
    try:
        return books_service.semantic_search(query, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/search/keyword",
    summary="BM25 sparse search — pure keyword matching on synthetic_document",
)
def keyword_search(
    query: str = Query(..., min_length=1),
    top_k: int = Query(default=BOOKS_DEFAULT_TOP_K, ge=1, le=50),
):
    try:
        return books_service.keyword_search(query, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/search/hybrid",
    summary="RRF fusion of dense (MiniLM) + sparse (BM25) with optional metadata filters",
)
def hybrid_search(
    query:     str        = Query(..., min_length=1),
    top_k:     int        = Query(default=BOOKS_DEFAULT_TOP_K, ge=1, le=50),
    genre:     str | None = Query(default=None),
    language:  str | None = Query(default=None),
    year_from: int | None = Query(default=None, ge=0, le=3000),
    year_to:   int | None = Query(default=None, ge=0, le=3000),
):
    try:
        return books_service.hybrid_search(query, top_k, genre, language, year_from, year_to)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/search/filtered",
    summary="Semantic search pre-filtered by genre, language, and/or year range",
)
def filtered_search(
    query:     str        = Query(..., min_length=1),
    genre:     str | None = Query(default=None),
    language:  str | None = Query(default=None),
    year_from: int | None = Query(default=None, ge=0, le=3000),
    year_to:   int | None = Query(default=None, ge=0, le=3000),
    top_k:     int        = Query(default=BOOKS_DEFAULT_TOP_K, ge=1, le=50),
):
    try:
        return books_service.filtered_search(query, genre, language, year_from, year_to, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/search/iterator",
    summary="Paginated semantic search — streams results in batches up to max_items",
    description=(
        "Useful for large-scale retrieval beyond the standard top_k limit. "
        "Results are fetched in pages of batch_size and accumulated until max_items is reached "
        "or the collection is exhausted."
    ),
)
def iterator_search(
    query:      str        = Query(..., min_length=1),
    genre:      str | None = Query(default=None),
    language:   str | None = Query(default=None),
    year_from:  int | None = Query(default=None, ge=0, le=3000),
    year_to:    int | None = Query(default=None, ge=0, le=3000),
    batch_size: int        = Query(default=20, ge=1, le=100),
    max_items:  int        = Query(default=100, ge=1, le=1000),
):
    try:
        return books_service.iterator_search(
            query, genre, language, year_from, year_to, batch_size, max_items
        )
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
        f"Default top_k is {BOOKS_DEFAULT_TOP_K}. "
        "Compare results against /search/semantic to see the effect."
    ),
)
def search_with_nprobe(
    query:  str = Query(..., min_length=1),
    nprobe: int = Query(..., ge=1, le=64, description="Number of IVF clusters to probe"),
    top_k:  int = Query(default=BOOKS_DEFAULT_TOP_K, ge=1, le=50),
):
    try:
        return books_service.search_with_nprobe(query, nprobe, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
