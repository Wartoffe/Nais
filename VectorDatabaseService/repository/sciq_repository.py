import time
from typing import Generator

from pymilvus import AnnSearchRequest, RRFRanker

from services.milvus_service import milvus_service
from config import SCIQ_COLLECTION, SCIQ_NPROBE

_OUTPUT_FIELDS = ["doc_id", "support_text", "question", "correct_answer", "support_length"]


class SciQRepository:

    def __init__(self):
        self._client = milvus_service.client
        self._collection = SCIQ_COLLECTION
        self._search_params = {"metric_type": "COSINE", "params": {"nprobe": SCIQ_NPROBE}}

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def insert(self, records: list[dict]) -> dict:
        return self._client.insert(collection_name=self._collection, data=records)

    def batch_insert(self, records: list[dict], batch_size: int = 100) -> list[dict]:
        results = []
        for i in range(0, len(records), batch_size):
            result = self._client.insert(
                collection_name=self._collection, data=records[i:i + batch_size]
            )
            results.append(result)
        return results

    def delete_by_id(self, entity_id: int) -> dict:
        return self._client.delete(collection_name=self._collection, ids=[entity_id])

    def batch_delete(self, entity_ids: list[int]) -> dict:
        return self._client.delete(collection_name=self._collection, ids=entity_ids)

    def find_by_id(self, entity_id: int) -> dict | None:
        rows = self._client.get(
            collection_name=self._collection,
            ids=[entity_id],
            output_fields=["id"] + _OUTPUT_FIELDS,
        )
        return rows[0] if rows else None

    def find_all(self, filter_expr: str = "", limit: int = 10, offset: int = 0) -> list[dict]:
        return self._client.query(
            collection_name=self._collection,
            filter=filter_expr or "",
            output_fields=["id"] + _OUTPUT_FIELDS,
            limit=limit,
            offset=offset,
        )

    def count(self, filter_expr: str = "") -> int:
        result = self._client.query(
            collection_name=self._collection,
            filter=filter_expr or "",
            output_fields=["count(*)"],
        )
        return int(result[0]["count(*)"]) if result else 0

    def iterate_all(self, batch_size: int = 100, filter_expr: str = "") -> Generator:
        """Cursor-based iteration over the entire collection — memory efficient for large datasets."""
        iterator = self._client.query_iterator(
            collection_name=self._collection,
            filter=filter_expr or "",
            output_fields=["id"] + _OUTPUT_FIELDS,
            batch_size=batch_size,
        )
        while True:
            batch = iterator.next()
            if not batch:
                iterator.close()
                break
            yield batch

    # ── Vector search ─────────────────────────────────────────────────────────

    def search(
        self,
        query_vectors: list[list[float]],
        top_k: int = 5,
        filter_expr: str = "",
    ) -> list[list[dict]]:
        """Dense ANN search on text_embedding (MiniLM COSINE)."""
        kwargs = dict(
            collection_name=self._collection,
            data=query_vectors,
            anns_field="text_embedding",
            search_params=self._search_params,
            limit=top_k,
            output_fields=["id"] + _OUTPUT_FIELDS,
        )
        if filter_expr:
            kwargs["filter"] = filter_expr
        return self._parse_hits(self._client.search(**kwargs))

    def keyword_search(self, query_text: str, top_k: int = 5) -> list[dict]:
        """BM25 sparse search — pure keyword matching, no dense vector."""
        raw = self._client.search(
            collection_name=self._collection,
            data=[query_text],
            anns_field="sparse",
            search_params={"metric_type": "BM25"},
            limit=top_k,
            output_fields=["id"] + _OUTPUT_FIELDS,
        )
        return self._parse_hits(raw)[0]

    def hybrid_search(
        self,
        query_text: str,
        query_vector: list[float],
        top_k: int = 5,
        filter_expr: str = "",
    ) -> list[dict]:
        """RRF fusion of dense (MiniLM) + sparse (BM25) search."""
        dense_req = AnnSearchRequest(
            data=[query_vector],
            anns_field="text_embedding",
            param={"metric_type": "COSINE", "params": {"nprobe": SCIQ_NPROBE}},
            limit=top_k,
            expr=filter_expr or None,
        )
        sparse_req = AnnSearchRequest(
            data=[query_text],
            anns_field="sparse",
            param={"metric_type": "BM25"},
            limit=top_k,
            expr=filter_expr or None,
        )
        raw = self._client.hybrid_search(
            collection_name=self._collection,
            reqs=[dense_req, sparse_req],
            ranker=RRFRanker(),
            limit=top_k,
            output_fields=["id"] + _OUTPUT_FIELDS,
        )
        return self._parse_hits([raw])[0]

    def search_with_text_match(
        self,
        query_vectors: list[list[float]],
        match_text: str,
        top_k: int = 5,
    ) -> list[list[dict]]:
        """Dense ANN pre-filtered by TEXT_MATCH on support_text (inverted token index)."""
        filter_expr = f"TEXT_MATCH(support_text, '{match_text}')"
        return self.search(query_vectors, top_k, filter_expr)

    def search_by_length_range(
        self,
        query_vectors: list[list[float]],
        min_length: int,
        max_length: int,
        top_k: int = 5,
    ) -> list[list[dict]]:
        filter_expr = f"support_length >= {min_length} && support_length <= {max_length}"
        return self.search(query_vectors, top_k, filter_expr)

    def search_by_doc_ids(
        self,
        query_vectors: list[list[float]],
        doc_ids: list[int],
        top_k: int = 5,
    ) -> list[list[dict]]:
        ids_str = ", ".join(map(str, doc_ids))
        filter_expr = f"doc_id in [{ids_str}]"
        return self.search(query_vectors, top_k, filter_expr)

    def search_with_metrics(
        self,
        query_vectors: list[list[float]],
        top_k: int = 5,
        filter_expr: str = "",
    ) -> tuple[list[list[dict]], dict]:
        start = time.perf_counter()
        results = self.search(query_vectors, top_k, filter_expr)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        metrics = {
            "search_time_ms": elapsed_ms,
            "num_queries": len(query_vectors),
            "top_k": top_k,
            "has_filter": bool(filter_expr),
        }
        return results, metrics

    def search_with_custom_nprobe(
        self,
        query_vectors: list[list[float]],
        nprobe: int,
        top_k: int = 5,
        filter_expr: str = "",
    ) -> list[list[dict]]:
        """Explicit nprobe — useful for demonstrating precision/speed trade-off in IVF_FLAT."""
        kwargs = dict(
            collection_name=self._collection,
            data=query_vectors,
            anns_field="text_embedding",
            search_params={"metric_type": "COSINE", "params": {"nprobe": nprobe}},
            limit=top_k,
            output_fields=["id"] + _OUTPUT_FIELDS,
        )
        if filter_expr:
            kwargs["filter"] = filter_expr
        return self._parse_hits(self._client.search(**kwargs))

    # ── Health & stats ────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        stats = self._client.get_collection_stats(self._collection)
        return {"collection": self._collection, "row_count": int(stats.get("row_count", 0))}

    def health_check(self) -> bool:
        try:
            self._client.get_collection_stats(self._collection)
            return True
        except Exception:
            return False

    def ensure_collection_loaded(self) -> None:
        self._client.load_collection(self._collection)

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_hits(raw) -> list[list[dict]]:
        results = []
        for hits in raw:
            batch = []
            for hit in hits:
                row = dict(hit.get("entity", {}))
                row["id"]    = hit.get("id")
                row["score"] = round(hit.get("distance", 0.0), 6)
                batch.append(row)
            results.append(batch)
        return results


sciq_repository = SciQRepository()
