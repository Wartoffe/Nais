import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from model.sciq_document import SciQDocumentCreate, SciQRagRequest
from schema.sciq_schema import sciq_schema, sciq_index_params
from service.impl.sciq_service import sciq_service
from services.milvus_service import milvus_service
from config import SCIQ_COLLECTION, SCIQ_DEFAULT_TOP_K

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/sciq", tags=["SciQ RAG"])


class DocIdsSearchRequest(BaseModel):
    query:   str       = Field(..., min_length=1)
    doc_ids: list[int] = Field(..., min_length=1, max_length=100)
    top_k:   int       = Field(default=SCIQ_DEFAULT_TOP_K, ge=1, le=50)


class BatchDeleteRequest(BaseModel):
    entity_ids: list[int] = Field(..., min_length=1, max_length=1000)


# ── Phase 0: Schema management ───────────────────────────────────────────────

@router.post("/schema/reset", summary="Drop and recreate the sciq_passages collection")
def reset_schema():
    client = milvus_service.client
    if client.has_collection(SCIQ_COLLECTION):
        client.drop_collection(SCIQ_COLLECTION)
    client.create_collection(
        collection_name=SCIQ_COLLECTION,
        schema=sciq_schema(client),
        index_params=sciq_index_params(client),
        consistency_level="Strong",
    )
    milvus_service.load_collection(SCIQ_COLLECTION)
    return {"status": "recreated", "collection": SCIQ_COLLECTION}


@router.get("/stats", summary="Collection row count and name")
def get_stats():
    try:
        return sciq_service.get_stats()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/health", summary="Milvus connectivity check for this collection")
def health_check():
    healthy = sciq_repository_health()
    return {"healthy": healthy, "collection": SCIQ_COLLECTION}


def sciq_repository_health() -> bool:
    from repository.sciq_repository import sciq_repository
    return sciq_repository.health_check()


# ── Phase 1: CRUD ─────────────────────────────────────────────────────────────

@router.post("/documents", summary="Insert a single passage document")
def create_document(doc: SciQDocumentCreate):
    try:
        return sciq_service.create_document(doc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/documents/batch", summary="Insert up to 100 passage documents in one call")
def batch_create(docs: list[SciQDocumentCreate]):
    try:
        return sciq_service.batch_create(docs)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/documents/{doc_id}", summary="Get passage by Milvus ID")
def get_document(doc_id: int):
    try:
        return sciq_service.get_document(doc_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/documents", summary="List passages with optional length filter")
def list_documents(
    min_length: int | None = Query(default=None, ge=0),
    max_length: int | None = Query(default=None, ge=0),
    limit:      int        = Query(default=20, ge=1, le=200),
    offset:     int        = Query(default=0, ge=0),
):
    try:
        return sciq_service.list_documents(min_length, max_length, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/documents/{doc_id}", summary="Delete passage by Milvus ID")
def delete_document(doc_id: int):
    try:
        return sciq_service.delete_document(doc_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/documents/batch", summary="Delete multiple passages by Milvus IDs")
def batch_delete(request: BatchDeleteRequest):
    try:
        return sciq_service.batch_delete(request.entity_ids)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Phase 2: Search ───────────────────────────────────────────────────────────

@router.get(
    "/search/semantic",
    summary="Dense ANN — MiniLM encodes query → cosine search on text_embedding",
)
def semantic_search(
    query: str = Query(..., min_length=1),
    top_k: int = Query(default=SCIQ_DEFAULT_TOP_K, ge=1, le=50),
):
    try:
        return sciq_service.semantic_search(query, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/search/keyword",
    summary="BM25 sparse search — pure keyword matching, no neural embedding",
)
def keyword_search(
    query: str = Query(..., min_length=1),
    top_k: int = Query(default=SCIQ_DEFAULT_TOP_K, ge=1, le=50),
):
    try:
        return sciq_service.keyword_search(query, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/search/hybrid",
    summary="RRF fusion of dense (MiniLM) + sparse (BM25) — combines semantic and keyword signals",
)
def hybrid_search(
    query: str = Query(..., min_length=1),
    top_k: int = Query(default=SCIQ_DEFAULT_TOP_K, ge=1, le=50),
):
    try:
        return sciq_service.hybrid_search(query, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/search/filtered",
    summary="Semantic search pre-filtered by passage length range",
)
def filtered_search(
    query:      str        = Query(..., min_length=1),
    min_length: int | None = Query(default=None, ge=0),
    max_length: int | None = Query(default=None, ge=0),
    top_k:      int        = Query(default=SCIQ_DEFAULT_TOP_K, ge=1, le=50),
):
    try:
        return sciq_service.filtered_search(query, min_length, max_length, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/search/text-match",
    summary="Dense ANN pre-filtered by TEXT_MATCH — requires specific term present in passage",
    description=(
        "`query` is encoded to a MiniLM vector for ANN ranking. "
        "`match_text` applies TEXT_MATCH(support_text) as a pre-filter using the inverted token index. "
        "Only passages containing the token(s) in match_text are candidates for ANN."
    ),
)
def text_match_search(
    query:      str = Query(..., min_length=1),
    match_text: str = Query(..., min_length=1, description="Keyword(s) that must appear in the passage"),
    top_k:      int = Query(default=SCIQ_DEFAULT_TOP_K, ge=1, le=50),
):
    try:
        return sciq_service.text_match_search(query, match_text, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/search/by-length",
    summary="Dense ANN filtered to passages with support_length between min and max",
)
def search_by_length_range(
    query:      str = Query(..., min_length=1),
    min_length: int = Query(..., ge=0),
    max_length: int = Query(..., ge=0),
    top_k:      int = Query(default=SCIQ_DEFAULT_TOP_K, ge=1, le=50),
):
    try:
        return sciq_service.search_by_length_range(query, min_length, max_length, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/search/by-doc-ids",
    summary="Dense ANN restricted to a specific set of doc_ids",
)
def search_by_doc_ids(request: DocIdsSearchRequest):
    try:
        return sciq_service.search_by_doc_ids(request.query, request.doc_ids, request.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/search/with-metrics",
    summary="Dense ANN + wall-clock timing — useful for benchmarking nprobe vs recall",
)
def search_with_metrics(
    query: str = Query(..., min_length=1),
    top_k: int = Query(default=SCIQ_DEFAULT_TOP_K, ge=1, le=50),
):
    try:
        return sciq_service.search_with_metrics(query, top_k)
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
        f"Default is {SCIQ_DEFAULT_TOP_K}. Compare results against /search/semantic to see the effect."
    ),
)
def search_with_nprobe(
    query:  str = Query(..., min_length=1),
    nprobe: int = Query(..., ge=1, le=64, description="Number of IVF clusters to probe"),
    top_k:  int = Query(default=SCIQ_DEFAULT_TOP_K, ge=1, le=50),
):
    try:
        return sciq_service.search_with_nprobe(query, nprobe, top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Phase 3: RAG pipeline ─────────────────────────────────────────────────────

@router.post(
    "/rag/query",
    summary="Full RAG retrieval: encode question → retrieve top-k passages → build context",
    description=(
        "Returns retrieved passages ranked by cosine similarity, a formatted context string "
        "ready for an LLM prompt, and an optional recall_hit flag when correct_answer is provided "
        "(True if the correct answer appears in any retrieved passage)."
    ),
)
def rag_query(request: SciQRagRequest):
    try:
        return sciq_service.rag_query(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
