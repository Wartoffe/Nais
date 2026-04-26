"""
Repository layer — direct access to the fashion_products Milvus collection.

"""

from services.milvus_service import milvus_service
from schema.milvus_schema import SCALAR_OUTPUT_FIELDS, fashion_schema, fashion_index_params
from config import FASHION_COLLECTION, NPROBE


class FashionRepository:
    """
    Data access layer for the fashion_products collection.
    """

    def __init__(self):
        self._client = milvus_service.client
        self._collection = FASHION_COLLECTION
        # Adjust 'ef' or 'nprobe' based on your index type (HNSW vs IVF)
        self._search_params = {
            "metric_type": "COSINE",
            "params": {"ef": NPROBE}  # Use 'nprobe' if using IVF index
        }

    # ── Insert / Upsert / Delete ───────────────────────────────────────────────

    def insert(self, records: list[dict]) -> dict:
        """Insert new records. Equivalent to save() / saveAll()."""
        result = self._client.insert(collection_name=self._collection, data=records)
        return {
            "insert_count": result.get("insert_count", 0),
            "ids": result.get("ids", [])
        }

    def upsert(self, records: dict | list[dict]) -> dict:
        """Update existing records. Milvus replaces the entire document."""
        data = [records] if isinstance(records, dict) else records
        result = self._client.upsert(collection_name=self._collection, data=data)
        return {
            "upsert_count": result.get("upsert_count", 0),
            "ids": result.get("ids", [])
        }

    def delete_by_id(self, entity_id: int) -> dict:
        """Delete a record by primary key."""
        result = self._client.delete(collection_name=self._collection, ids=[entity_id])
        return {
            "delete_count": result.get("delete_count", 0)
        }

    # ── Retrieval by ID ────────────────────────────────────────────────────────

    def find_by_id(self, entity_id: int, output_fields: list[str] | None = None) -> dict | None:
        """
        Retrieves a single record by its Milvus primary key.
        """
        fields = output_fields or SCALAR_OUTPUT_FIELDS
        rows = self._client.get(
            collection_name=self._collection,
            ids=[entity_id],
            output_fields=fields,
        )
        return rows[0] if rows else None

    def find_by_id_with_vectors(self, entity_id: int) -> dict | None:
        """Retrieves a record along with text_embedding and image_embedding vectors."""
        return self.find_by_id(
            entity_id,
            output_fields=SCALAR_OUTPUT_FIELDS + ["text_embedding", "image_embedding"],
        )

    # ── Scalar Search (Non-vector) ───────────────────────────────────────────

    def find_all(
        self,
        filter_expr: str = "",
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """
        Pure scalar search without vector ranking.
        
        The filter_expr parameter is a Milvus boolean expression, e.g.:
          'gender == "Men" && base_colour == "Blue"'
          'year >= 2011 && year <= 2015'
          'master_category in ["Apparel", "Footwear"]'
        """
        return self._client.query(
            collection_name=self._collection,
            filter=filter_expr or "",
            output_fields=SCALAR_OUTPUT_FIELDS,
            limit=limit,
            offset=offset,
        )

    def count(self, filter_expr: str = "") -> int:
        """
        Counts records that satisfy the filter condition.
        
        """
        result = self._client.query(
            collection_name=self._collection,
            filter=filter_expr or "",
            output_fields=["count(*)"],
        )
        return int(result[0]["count(*)"]) if result else 0

    # ── ANN Vector Search ─────────────────────────────────────────────────

    def search(
        self,
        query_vectors: list[list[float]],
        anns_field: str,
        top_k: int = 10,
        filter_expr: str = "",
        include_vectors: bool = False,
    ) -> list[list[dict]]:
        """
        ANN search over a single vector field.

        Parameters
        ----------
        query_vectors : list[list[float]]
            List of query vectors — one or more (batch search).
        anns_field : str
            'text_embedding' or 'image_embedding'
        top_k : int
            Number of results per query vector.
        filter_expr : str
            Milvus boolean expression applied BEFORE ANN search (pre-filtering).
        include_vectors : bool
            If True, returns stored embeddings alongside each hit.

        Returns
        -------
        list[list[dict]]
            One inner list per query vector.
        """
        fields = list(SCALAR_OUTPUT_FIELDS)
        if include_vectors:
            fields += ["text_embedding", "image_embedding"]

        raw = self._client.search(
            collection_name=self._collection,
            data=query_vectors,
            anns_field=anns_field,
            search_params=self._search_params,
            limit=top_k,
            filter=filter_expr,
            output_fields=fields,
            consistency_level="Strong"
        )

        results = []
        for hits in raw:
            batch = []
            for hit in hits:
                row = {"id": hit["id"], "score": round(hit["distance"], 4)}
                row.update(hit.get("entity", {}))
                batch.append(row)
            results.append(batch)
        return results

    # ── Collection Management ─────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Returns collection statistics (row_count, etc.)."""
        return self._client.get_collection_stats(collection_name=self._collection)

    def reset(self) -> None:
        """
        Drops and recreates the collection with all indexes.
        Should only be used for resetting demo environments.
        """
        schema = fashion_schema(self._client)
        idx = fashion_index_params(self._client)
        if self._client.has_collection(self._collection):
            self._client.drop_collection(self._collection)
        self._client.create_collection(
            collection_name=self._collection,
            schema=schema,
            index_params=idx,
            consistency_level="Strong",
        )
        self._client.load_collection(self._collection)


# Module-level singleton
fashion_repository = FashionRepository()