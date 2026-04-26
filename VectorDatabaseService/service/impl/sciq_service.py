import logging

from model.sciq_document import SciQDocumentCreate, SciQRagRequest, SciQRagResult, SciQSearchResult
from repository.sciq_repository import sciq_repository
from service.i_sciq_service import ISciQService
from services.minilm_embedding_service import minilm_service

logger = logging.getLogger(__name__)


def _length_filter(min_length: int | None, max_length: int | None) -> str:
    parts = []
    if min_length is not None:
        parts.append(f"support_length >= {min_length}")
    if max_length is not None:
        parts.append(f"support_length <= {max_length}")
    return " && ".join(parts)


def _to_record(doc: SciQDocumentCreate, doc_id: int = 0) -> tuple[dict, list[float]]:
    """Returns (metadata_dict_without_embedding, text_to_encode)."""
    text = doc.support_text.strip()
    return {
        "doc_id":         doc_id,
        "support_text":   text[:1999],
        "question":       doc.question.strip()[:999],
        "correct_answer": doc.correct_answer.strip()[:499],
        "support_length": len(text),
    }, text


def _to_search_result(row: dict) -> SciQSearchResult:
    return SciQSearchResult(
        id=row["id"],
        doc_id=row.get("doc_id", 0),
        support_text=row.get("support_text", ""),
        question=row.get("question", ""),
        correct_answer=row.get("correct_answer", ""),
        support_length=row.get("support_length", 0),
        score=row.get("score", 0.0),
    )


class SciQService(ISciQService):

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def create_document(self, doc: SciQDocumentCreate) -> dict:
        if not doc.support_text.strip():
            raise ValueError("support_text cannot be empty")
        record, text = _to_record(doc)
        record["text_embedding"] = minilm_service.encode_one(text)
        result = sciq_repository.insert([record])
        return {"inserted_ids": result.get("ids", []), "insert_count": result.get("insert_count", 0)}

    def batch_create(self, docs: list[SciQDocumentCreate]) -> dict:
        if not docs:
            raise ValueError("docs list cannot be empty")
        if len(docs) > 100:
            raise ValueError("maximum 100 documents per batch")

        records, texts = [], []
        for doc in docs:
            if not doc.support_text.strip():
                raise ValueError("support_text cannot be empty in all documents")
            record, text = _to_record(doc)
            records.append(record)
            texts.append(text)

        embeddings = minilm_service.encode(texts)
        for record, emb in zip(records, embeddings):
            record["text_embedding"] = emb

        batch_results = sciq_repository.batch_insert(records)
        total_inserted = sum(r.get("insert_count", 0) for r in batch_results)
        all_ids = [_id for r in batch_results for _id in r.get("ids", [])]
        return {"inserted_ids": all_ids, "insert_count": total_inserted}

    def get_document(self, doc_id: int) -> dict:
        row = sciq_repository.find_by_id(doc_id)
        if row is None:
            raise KeyError(f"Document {doc_id} not found")
        return row

    def list_documents(self, min_length: int | None, max_length: int | None, limit: int, offset: int) -> list[dict]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        if offset < 0:
            raise ValueError("offset cannot be negative")
        return sciq_repository.find_all(
            filter_expr=_length_filter(min_length, max_length),
            limit=limit,
            offset=offset,
        )

    def delete_document(self, doc_id: int) -> dict:
        result = sciq_repository.delete_by_id(doc_id)
        return {"deleted_id": doc_id, "delete_count": result.get("delete_count", 0)}

    def batch_delete(self, entity_ids: list[int]) -> dict:
        if not entity_ids:
            raise ValueError("entity_ids cannot be empty")
        result = sciq_repository.batch_delete(entity_ids)
        return {"deleted_ids": entity_ids, "delete_count": result.get("delete_count", 0)}

    # ── Search ────────────────────────────────────────────────────────────────

    def semantic_search(self, query: str, top_k: int) -> list[dict]:
        if not query.strip():
            raise ValueError("query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        qvec = minilm_service.encode_one(query)
        return sciq_repository.search([qvec], top_k=top_k)[0]

    def keyword_search(self, query: str, top_k: int) -> list[dict]:
        """BM25 sparse search — ranks by exact term frequency, no semantic similarity."""
        if not query.strip():
            raise ValueError("query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        return sciq_repository.keyword_search(query, top_k=top_k)

    def hybrid_search(self, query: str, top_k: int) -> list[dict]:
        """Dense (MiniLM) + BM25 via Reciprocal Rank Fusion — best of both worlds."""
        if not query.strip():
            raise ValueError("query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        qvec = minilm_service.encode_one(query)
        return sciq_repository.hybrid_search(query, qvec, top_k=top_k)

    def filtered_search(self, query: str, min_length: int | None, max_length: int | None, top_k: int) -> list[dict]:
        if not query.strip():
            raise ValueError("query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        filter_expr = _length_filter(min_length, max_length)
        qvec = minilm_service.encode_one(query)
        return sciq_repository.search([qvec], top_k=top_k, filter_expr=filter_expr)[0]

    def text_match_search(self, query: str, match_text: str, top_k: int) -> list[dict]:
        """ANN pre-filtered by TEXT_MATCH — inverted token index, fast exact-term check."""
        if not query.strip():
            raise ValueError("query cannot be empty")
        if not match_text.strip():
            raise ValueError("match_text cannot be empty")
        qvec = minilm_service.encode_one(query)
        return sciq_repository.search_with_text_match([qvec], match_text.strip(), top_k=top_k)[0]

    def search_by_length_range(self, query: str, min_length: int, max_length: int, top_k: int) -> list[dict]:
        if min_length > max_length:
            raise ValueError("min_length must be <= max_length")
        qvec = minilm_service.encode_one(query)
        return sciq_repository.search_by_length_range([qvec], min_length, max_length, top_k=top_k)[0]

    def search_by_doc_ids(self, query: str, doc_ids: list[int], top_k: int) -> list[dict]:
        if not doc_ids:
            raise ValueError("doc_ids cannot be empty")
        if not query.strip():
            raise ValueError("query cannot be empty")
        qvec = minilm_service.encode_one(query)
        return sciq_repository.search_by_doc_ids([qvec], doc_ids, top_k=top_k)[0]

    def search_with_metrics(self, query: str, top_k: int) -> dict:
        if not query.strip():
            raise ValueError("query cannot be empty")
        qvec = minilm_service.encode_one(query)
        results, metrics = sciq_repository.search_with_metrics([qvec], top_k=top_k)
        return {"results": results[0], "metrics": metrics}

    def search_with_nprobe(self, query: str, nprobe: int, top_k: int) -> list[dict]:
        if not query.strip():
            raise ValueError("query cannot be empty")
        if nprobe < 1:
            raise ValueError("nprobe must be >= 1")
        qvec = minilm_service.encode_one(query)
        return sciq_repository.search_with_custom_nprobe([qvec], nprobe=nprobe, top_k=top_k)[0]

    # ── RAG ───────────────────────────────────────────────────────────────────

    def rag_query(self, request: SciQRagRequest) -> SciQRagResult:
        if not request.question.strip():
            raise ValueError("question cannot be empty")

        hits = self.semantic_search(request.question, request.top_k)
        passages = [_to_search_result(h) for h in hits]

        context = "\n\n".join(
            f"Passage {i + 1} (score={p.score:.4f}):\n{p.support_text}"
            for i, p in enumerate(passages)
        )

        recall_hit = None
        if request.correct_answer:
            answer_lower = request.correct_answer.lower()
            recall_hit = any(answer_lower in p.support_text.lower() for p in passages)

        return SciQRagResult(
            question=request.question,
            top_k=request.top_k,
            retrieved_passages=passages,
            context=context,
            recall_hit=recall_hit,
            correct_answer=request.correct_answer,
        )

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        return sciq_repository.get_stats()


sciq_service = SciQService()
