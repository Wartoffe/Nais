from typing import Generator

from config import BOOK_REVIEWS_COLLECTION, REVIEWS_NPROBE
from schema.reviews_schema import REVIEWS_OUTPUT_FIELDS
from services.milvus_service import milvus_service


def _sanitize_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


class ReviewsRepository:

    def __init__(self):
        self._client = milvus_service.client
        self._collection = BOOK_REVIEWS_COLLECTION
        self._search_params = {"metric_type": "COSINE", "params": {"nprobe": REVIEWS_NPROBE}}

    # CRUD
    def insert(self, records: list[dict]) -> dict:
        return self._client.insert(collection_name=self._collection, data=records)

    def upsert(self, records: dict | list[dict]) -> dict:
        data = [records] if isinstance(records, dict) else records
        return self._client.upsert(collection_name=self._collection, data=data)

    def delete_by_id(self, entity_id: int) -> dict:
        return self._client.delete(collection_name=self._collection, ids=[entity_id])

    def batch_delete(self, entity_ids: list[int]) -> dict:
        return self._client.delete(collection_name=self._collection, ids=entity_ids)

    def find_by_id(self, entity_id: int, output_fields: list[str] | None = None) -> dict | None:
        fields = output_fields or ["id"] + REVIEWS_OUTPUT_FIELDS
        rows = self._client.get(
            collection_name=self._collection,
            ids=[entity_id],
            output_fields=fields,
        )
        return rows[0] if rows else None

    def find_by_id_for_update(self, entity_id: int) -> dict | None:
        fields = ["id"] + REVIEWS_OUTPUT_FIELDS + ["review_embedding"]
        rows = self._client.get(
            collection_name=self._collection,
            ids=[entity_id],
            output_fields=fields,
        )
        return rows[0] if rows else None

    def find_by_review_id(self, review_id: str) -> dict | None:
        rows = self._client.query(
            collection_name=self._collection,
            filter=f'review_id == "{_sanitize_string(review_id)}"',
            output_fields=["id"] + REVIEWS_OUTPUT_FIELDS,
            limit=1,
        )
        return rows[0] if rows else None

    def find_all(self, filter_expr: str = "", limit: int = 20, offset: int = 0) -> list[dict]:
        return self._client.query(
            collection_name=self._collection,
            filter=filter_expr or "",
            output_fields=["id"] + REVIEWS_OUTPUT_FIELDS,
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
        iterator = self._client.query_iterator(
            collection_name=self._collection,
            filter=filter_expr or "",
            output_fields=["id"] + REVIEWS_OUTPUT_FIELDS,
            batch_size=batch_size,
        )
        while True:
            batch = iterator.next()
            if not batch:
                iterator.close()
                break
            yield batch

    def update_by_id(self, entity_id: int, updated_fields: dict) -> dict:
        current = self.find_by_id_for_update(entity_id)
        if current is None:
            raise KeyError(f"Review {entity_id} not found")

        merged = dict(current)
        merged.update(updated_fields)
        merged["id"] = entity_id

        result = self.upsert(merged)
        return {
            "upsert_count": result.get("upsert_count", 0),
            "ids": result.get("ids", []),
        }

    # Search
    def search_semantic(
        self,
        query_vectors: list[list[float]],
        top_k: int = 5,
        filter_expr: str = "",
    ) -> list[list[dict]]:
        kwargs = {
            "collection_name": self._collection,
            "data": query_vectors,
            "anns_field": "review_embedding",
            "search_params": self._search_params,
            "limit": top_k,
            "output_fields": ["id"] + REVIEWS_OUTPUT_FIELDS,
        }
        if filter_expr:
            kwargs["filter"] = filter_expr
        return self._parse_hits(self._client.search(**kwargs))

    def search_with_custom_nprobe(
        self,
        query_vectors: list[list[float]],
        nprobe: int,
        top_k: int = 5,
        filter_expr: str = "",
    ) -> list[list[dict]]:
        kwargs = {
            "collection_name": self._collection,
            "data": query_vectors,
            "anns_field": "review_embedding",
            "search_params": {"metric_type": "COSINE", "params": {"nprobe": nprobe}},
            "limit": top_k,
            "output_fields": ["id"] + REVIEWS_OUTPUT_FIELDS,
        }
        if filter_expr:
            kwargs["filter"] = filter_expr
        return self._parse_hits(self._client.search(**kwargs))

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

    @staticmethod
    def _parse_hits(raw) -> list[list[dict]]:
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


reviews_repository = ReviewsRepository()
