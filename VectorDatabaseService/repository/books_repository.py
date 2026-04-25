"""Milvus repository for the books collection.

Covers all data-access operations used by BooksService:
  CRUD   : insert, upsert, find_by_id, find_by_isbn, find_all, delete_by_id
  Search : search_dense, search_dense_with_offset,
           keyword_search, hybrid_search, search_with_custom_nprobe
  Util   : get_stats, health_check, find_by_id_for_update
"""

import logging
from typing import Generator

from pymilvus import AnnSearchRequest, RRFRanker

from config import BOOKS_COLLECTION, BOOKS_NPROBE
from schema.books_schema import BOOKS_OUTPUT_FIELDS
from services.milvus_service import milvus_service

logger = logging.getLogger(__name__)

_SANITIZE = str.maketrans({"\\": "\\\\", '"': '\\"'})


def _s(value: str) -> str:
    return value.translate(_SANITIZE)


class BooksRepository:

    def __init__(self):
        self._collection = BOOKS_COLLECTION
        self._search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": BOOKS_NPROBE},
        }

    @property
    def _client(self):
        # Property so hot-reload / test mocks work without re-instantiating.
        return milvus_service.client

    # ------------------------------------------------------------------ #
    #  CRUD                                                                #
    # ------------------------------------------------------------------ #

    def insert(self, records: list[dict]) -> dict:
        """Insert one or more records.

        Each record must already contain:
          - all scalar fields
          - synthetic_document  (pre-built by the service layer)
          - dense_embedding     (MiniLM vector of synthetic_document)

        BM25 sparse vectors are generated automatically by the BM25
        function defined in the collection schema on ``synthetic_document``.
        """
        return self._client.insert(
            collection_name=self._collection,
            data=records,
        )

    def upsert(self, records: dict | list[dict]) -> dict:
        data = [records] if isinstance(records, dict) else records
        return self._client.upsert(
            collection_name=self._collection,
            data=data,
        )

    def delete_by_id(self, entity_id: int) -> dict:
        return self._client.delete(
            collection_name=self._collection,
            ids=[entity_id],
        )

    def batch_delete(self, entity_ids: list[int]) -> dict:
        return self._client.delete(
            collection_name=self._collection,
            ids=entity_ids,
        )

    # ------------------------------------------------------------------ #
    #  Point / scalar reads                                               #
    # ------------------------------------------------------------------ #

    def find_by_id(
        self,
        entity_id: int,
        output_fields: list[str] | None = None,
    ) -> dict | None:
        """Simple lookup — used for GET /books/{id}."""
        fields = output_fields or (["id"] + BOOKS_OUTPUT_FIELDS)
        rows = self._client.get(
            collection_name=self._collection,
            ids=[entity_id],
            output_fields=fields,
        )
        return rows[0] if rows else None

    def find_by_id_for_update(self, entity_id: int) -> dict | None:
        """Fetch all persisted fields (including synthetic_document and
        dense_embedding) so the service can merge and re-embed on update."""
        fields = ["id"] + BOOKS_OUTPUT_FIELDS + ["synthetic_document", "dense_embedding"]
        rows = self._client.get(
            collection_name=self._collection,
            ids=[entity_id],
            output_fields=fields,
        )
        return rows[0] if rows else None

    def find_by_isbn(self, isbn: str) -> dict | None:
        """Simple lookup — used for GET /books/isbn/{isbn}."""
        rows = self._client.query(
            collection_name=self._collection,
            filter=f'isbn == "{_s(isbn)}"',
            output_fields=["id"] + BOOKS_OUTPUT_FIELDS,
            limit=1,
        )
        return rows[0] if rows else None

    def find_all(
        self,
        filter_expr: str = "",
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        return self._client.query(
            collection_name=self._collection,
            filter=filter_expr or "",
            output_fields=["id"] + BOOKS_OUTPUT_FIELDS,
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

    def iterate_all(
        self,
        batch_size: int = 100,
        filter_expr: str = "",
    ) -> Generator:
        """Cursor-based full scan — useful for exports and re-indexing."""
        iterator = self._client.query_iterator(
            collection_name=self._collection,
            filter=filter_expr or "",
            output_fields=["id"] + BOOKS_OUTPUT_FIELDS,
            batch_size=batch_size,
        )
        while True:
            batch = iterator.next()
            if not batch:
                iterator.close()
                break
            yield batch

    # ------------------------------------------------------------------ #
    #  Vector search                                                       #
    # ------------------------------------------------------------------ #

    def search_dense(
        self,
        query_vectors: list[list[float]],
        top_k: int = 5,
        filter_expr: str = "",
    ) -> list[list[dict]]:
        """Single-vector ANN over dense_embedding (cosine / IVF_FLAT).

        Simple query: search by book description.
        """
        kwargs = dict(
            collection_name=self._collection,
            data=query_vectors,
            anns_field="dense_embedding",
            search_params=self._search_params,
            limit=top_k,
            output_fields=["id"] + BOOKS_OUTPUT_FIELDS,
        )
        if filter_expr:
            kwargs["filter"] = filter_expr
        return self._parse_hits(self._client.search(**kwargs))

    def search_dense_with_offset(
        self,
        query_vectors: list[list[float]],
        top_k: int = 5,
        offset: int = 0,
        filter_expr: str = "",
    ) -> list[list[dict]]:
        """Paginated dense search — used by the iterator endpoint.

        Complex query: vector + filter with iterator.
        Caller accumulates pages until max_items is reached or results
        are exhausted.
        """
        kwargs = dict(
            collection_name=self._collection,
            data=query_vectors,
            anns_field="dense_embedding",
            search_params=self._search_params,
            limit=top_k,
            offset=offset,
            output_fields=["id"] + BOOKS_OUTPUT_FIELDS,
        )
        if filter_expr:
            kwargs["filter"] = filter_expr
        return self._parse_hits(self._client.search(**kwargs))

    def keyword_search(
        self,
        query_text: str,
        top_k: int = 5,
        filter_expr: str = "",
    ) -> list[dict]:
        """Pure BM25 sparse search over synthetic_document.

        Milvus auto-generates the sparse vector from ``query_text``
        using the same BM25 function that was applied at insert time.
        """
        kwargs = dict(
            collection_name=self._collection,
            data=[query_text],
            anns_field="sparse",
            search_params={"metric_type": "BM25"},
            limit=top_k,
            output_fields=["id"] + BOOKS_OUTPUT_FIELDS,
        )
        if filter_expr:
            kwargs["filter"] = filter_expr
        return self._parse_hits(self._client.search(**kwargs))[0]

    def hybrid_search(
        self,
        query_text: str,
        query_vector: list[float],
        top_k: int = 5,
        filter_expr: str = "",
    ) -> list[dict]:
        """RRF fusion of dense (MiniLM cosine) + sparse (BM25).

        Complex query: hybrid dense + BM25.
        Both legs share the same optional metadata filter so results
        are consistent before fusion.
        """
        expr = filter_expr or None

        dense_req = AnnSearchRequest(
            data=[query_vector],
            anns_field="dense_embedding",
            param={"metric_type": "COSINE", "params": {"nprobe": BOOKS_NPROBE}},
            limit=top_k,
            expr=expr,
        )
        sparse_req = AnnSearchRequest(
            data=[query_text],
            anns_field="sparse",
            param={"metric_type": "BM25"},
            limit=top_k,
            expr=expr,
        )
        raw = self._client.hybrid_search(
            collection_name=self._collection,
            reqs=[dense_req, sparse_req],
            ranker=RRFRanker(),
            limit=top_k,
            output_fields=["id"] + BOOKS_OUTPUT_FIELDS,
        )
        return self._parse_hits([raw])[0]

    def search_with_custom_nprobe(
        self,
        query_vectors: list[list[float]],
        nprobe: int,
        top_k: int = 5,
        filter_expr: str = "",
    ) -> list[list[dict]]:
        """Dense search with caller-controlled nprobe for tuning demos."""
        kwargs = dict(
            collection_name=self._collection,
            data=query_vectors,
            anns_field="dense_embedding",
            search_params={"metric_type": "COSINE", "params": {"nprobe": nprobe}},
            limit=top_k,
            output_fields=["id"] + BOOKS_OUTPUT_FIELDS,
        )
        if filter_expr:
            kwargs["filter"] = filter_expr
        return self._parse_hits(self._client.search(**kwargs))

    # ------------------------------------------------------------------ #
    #  Util                                                                #
    # ------------------------------------------------------------------ #

    def get_stats(self) -> dict:
        stats = self._client.get_collection_stats(self._collection)
        return {
            "collection": self._collection,
            "row_count": int(stats.get("row_count", 0)),
        }

    def health_check(self) -> bool:
        try:
            self._client.get_collection_stats(self._collection)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    #  Internal                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_hits(raw) -> list[list[dict]]:
        """Normalize pymilvus SearchResult into plain list[list[dict]]."""
        results = []
        for hits in raw:
            batch = []
            for hit in hits:
                row = dict(hit.get("entity", {}))
                row["id"] = hit.get("id")
                row["score"] = round(hit.get("distance", 0.0), 6)
                batch.append(row)
            results.append(batch)
        return results


books_repository = BooksRepository()