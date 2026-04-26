from pymilvus import AnnSearchRequest, RRFRanker, WeightedRanker

from services.milvus_service import milvus_service
from config import LAB_COLLECTION, LAB_NPROBE

LAB_OUTPUT_FIELDS = [
    "product_name", "gender", "master_category",
    "sub_category", "article_type", "base_colour",
    "season", "year", "usage", "has_image",
]


class FashionLabRepository:

    def __init__(self):
        self._client = milvus_service.client
        self._collection = LAB_COLLECTION
        self._search_params = {"metric_type": "COSINE", "params": {"nprobe": LAB_NPROBE}}

    def insert(self, records: list[dict]) -> dict:
        """Insert one or more records into the lab collection."""
        return self._client.insert(collection_name=self._collection, data=records)

    def delete_by_id(self, entity_id: int) -> dict:
        """Delete a record by its Milvus ID."""
        return self._client.delete(collection_name=self._collection, ids=[entity_id])

    def find_by_id(self, entity_id: int) -> dict | None:
        """Retrieve a single record by its Milvus primary key."""
        rows = self._client.get(
            collection_name=self._collection,
            ids=[entity_id],
            output_fields=["id"] + LAB_OUTPUT_FIELDS,
        )
        return rows[0] if rows else None

    def find_all(self, filter_expr: str = "", limit: int = 10, offset: int = 0) -> list[dict]:
        """
        Pure scalar search — no vector ranking involved.
        filter_expr examples:
          'gender == "Men"'
          'base_colour in ["Blue", "Black"]'
          '(season == "Summer" || season == "Spring") && has_image == true'
        """
        return self._client.query(
            collection_name=self._collection,
            filter=filter_expr or "",
            output_fields=["id"] + LAB_OUTPUT_FIELDS,
            limit=limit,
            offset=offset,
        )

    def count(self, filter_expr: str = "") -> int:
        """Counts records that satisfy the given condition."""
        result = self._client.query(
            collection_name=self._collection,
            filter=filter_expr or "",
            output_fields=["count(*)"],
        )
        return int(result[0]["count(*)"]) if result else 0

    def search(
        self,
        query_vectors: list[list[float]],
        anns_field: str,
        top_k: int = 5,
        filter_expr: str = "",
    ) -> list[list[dict]]:
        """
        ANN search over a single vector field.

        anns_field:
          'text_embedding'  → Semantic text search
          'image_embedding' → Visual similarity search

        Cross-modal retrieval is achieved via combinations:
          text vector  + 'image_embedding' → text-to-image
          image vector + 'text_embedding'  → image-to-text
        """
        raw = self._client.search(
            collection_name=self._collection,
            data=query_vectors,
            anns_field=anns_field,
            search_params=self._search_params,
            limit=top_k,
            filter=filter_expr,
            output_fields=LAB_OUTPUT_FIELDS,
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

    def search_with_offset(
        self,
        query_vectors: list[list[float]],
        anns_field: str,
        top_k: int,
        offset: int = 0,
    ) -> list[list[dict]]:
        """ANN search with an offset parameter for result pagination."""
        raw = self._client.search(
            collection_name=self._collection,
            data=query_vectors,
            anns_field=anns_field,
            search_params=self._search_params,
            limit=top_k,
            offset=offset,
            output_fields=LAB_OUTPUT_FIELDS,
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

    def search_grouped(
        self,
        query_vectors: list[list[float]],
        anns_field: str,
        top_k: int,
        group_by_field: str,
        group_size: int = 1,
    ) -> list[list[dict]]:
        """
        Grouped ANN search — returns a maximum of group_size results per 
        group_by_field value, ensuring result diversity.
        """
        raw = self._client.search(
            collection_name=self._collection,
            data=query_vectors,
            anns_field=anns_field,
            search_params=self._search_params,
            limit=top_k,
            group_by_field=group_by_field,
            group_size=group_size,
            output_fields=LAB_OUTPUT_FIELDS,
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

    def search_range(
        self,
        query_vectors: list[list[float]],
        anns_field: str,
        radius: float,
        range_filter: float,
        top_k: int = 100,
    ) -> list[list[dict]]:
        """
        Range search — returns all results where the COSINE score falls within the
        range [radius, range_filter]. For COSINE: radius=min_score, range_filter=max_score.
        """
        params = {
            "metric_type": "COSINE",
            "params": {
                "nprobe": LAB_NPROBE,
                "radius": radius,
                "range_filter": range_filter,
            },
        }
        raw = self._client.search(
            collection_name=self._collection,
            data=query_vectors,
            anns_field=anns_field,
            search_params=params,
            limit=top_k,
            output_fields=LAB_OUTPUT_FIELDS,
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

    def search_with_consistency(
        self,
        query_vectors: list[list[float]],
        anns_field: str,
        top_k: int,
        consistency_level: str,
    ) -> list[list[dict]]:
        """ANN search with an explicit consistency level."""
        raw = self._client.search(
            collection_name=self._collection,
            data=query_vectors,
            anns_field=anns_field,
            search_params=self._search_params,
            limit=top_k,
            consistency_level=consistency_level,
            output_fields=LAB_OUTPUT_FIELDS,
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

    def hybrid_search_weighted(
        self,
        query_vector: list[float],
        top_k: int,
        text_weight: float,
        image_weight: float,
    ) -> list[dict]:
        """
        Hybrid search using WeightedRanker — applies explicit weights per field.
        Note: Unlike RRFRanker, weights are directly proportional to scores rather than ranks.
        """
        req_params = {"metric_type": "COSINE", "params": {"nprobe": LAB_NPROBE}}
        req1 = AnnSearchRequest(
            data=[query_vector], anns_field="text_embedding",
            param=req_params, limit=top_k,
        )
        req2 = AnnSearchRequest(
            data=[query_vector], anns_field="image_embedding",
            param=req_params, limit=top_k,
        )
        raw = self._client.hybrid_search(
            collection_name=self._collection,
            reqs=[req1, req2],
            ranker=WeightedRanker(text_weight, image_weight),
            limit=top_k,
            output_fields=LAB_OUTPUT_FIELDS,
        )
        results = []
        for hit in raw:
            row = {"id": hit["id"], "score": round(hit["distance"], 4)}
            row.update(hit.get("entity", {}))
            results.append(row)
        return results

    def hybrid_search(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Hybrid search using RRFRanker — searches both text_embedding and image_embedding
        simultaneously and merges results with Reciprocal Rank Fusion.
        """
        req_params = {"metric_type": "COSINE", "params": {"nprobe": LAB_NPROBE}}
        req1 = AnnSearchRequest(
            data=[query_vector], anns_field="text_embedding",
            param=req_params, limit=top_k,
        )
        req2 = AnnSearchRequest(
            data=[query_vector], anns_field="image_embedding",
            param=req_params, limit=top_k,
        )
        raw = self._client.hybrid_search(
            collection_name=self._collection,
            reqs=[req1, req2],
            ranker=RRFRanker(),
            limit=top_k,
            output_fields=LAB_OUTPUT_FIELDS,
        )
        results = []
        for hit in raw:
            row = {"id": hit["id"], "score": round(hit["distance"], 4)}
            row.update(hit.get("entity", {}))
            results.append(row)
        return results

    def search_in_partition(
        self,
        query_vectors: list[list[float]],
        anns_field: str,
        top_k: int,
        partition_names: list[str],
    ) -> list[list[dict]]:
        """ANN search restricted to specific partitions."""
        raw = self._client.search(
            collection_name=self._collection,
            data=query_vectors,
            anns_field=anns_field,
            search_params=self._search_params,
            limit=top_k,
            partition_names=partition_names,
            output_fields=LAB_OUTPUT_FIELDS,
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

    def search_with_nprobe(
        self,
        query_vectors: list[list[float]],
        anns_field: str,
        top_k: int,
        nprobe: int,
    ) -> list[list[dict]]:
        """ANN search with an explicit nprobe value (overrides default)."""
        search_params = {"metric_type": "COSINE", "params": {"nprobe": nprobe}}
        raw = self._client.search(
            collection_name=self._collection,
            data=query_vectors,
            anns_field=anns_field,
            search_params=search_params,
            limit=top_k,
            output_fields=LAB_OUTPUT_FIELDS,
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

    def get_facets(self, fields: list[str]) -> dict:
        """
        Faceted aggregation — counts occurrences per value for each given field.
        Achieved by querying all rows and counting in Python (Milvus has no GROUP BY).
        """
        rows = self._client.query(
            collection_name=self._collection,
            filter="",
            output_fields=fields,
            limit=16384,
        )
        facets: dict[str, dict[str, int]] = {f: {} for f in fields}
        for row in rows:
            for field in fields:
                val = row.get(field, "")
                if val:
                    facets[field][val] = facets[field].get(val, 0) + 1
        # Sort each facet by count descending
        return {
            field: dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
            for field, counts in facets.items()
        }

    def random_sample(self, sample_size: int) -> list[dict]:
        """Returns a pseudo-random sample by fetching with a high limit and slicing."""
        import random
        rows = self._client.query(
            collection_name=self._collection,
            filter="",
            output_fields=LAB_OUTPUT_FIELDS,
            limit=min(sample_size * 10, 1000),
        )
        if len(rows) <= sample_size:
            return rows
        return random.sample(rows, sample_size)

    def get_stats(self) -> dict:
        """Returns collection statistics (row_count, etc.)."""
        stats = self._client.get_collection_stats(collection_name=self._collection)
        return {"collection": self._collection, "row_count": int(stats.get("row_count", 0))}


fashion_lab_repository = FashionLabRepository()