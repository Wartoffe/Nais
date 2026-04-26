"""
Concrete implementation of IFashionService for the fashion_products collection.

Contains all business logic:
  - CLIP encoding (text and images)
  - Building Milvus filter expressions
  - ANN search (single-modal, cross-modal, batch)
  - Reciprocal Rank Fusion for multimodal searches
  - Two-stage pipeline (visual recall + text reranking)

The repository layer (FashionRepository) is called for all I/O with Milvus.
"""

import logging

import numpy as np

from model.fashion_product import (
    FashionProduct,
    FashionProductCreate,
    FashionProductUpdate,
    SearchResult,
)
from repository.fashion_repository import fashion_repository
from schema.milvus_schema import SCALAR_OUTPUT_FIELDS
from service.i_fashion_service import IFashionService
from services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


# ── Helper functions (pure business logic) ───────────────────────────────────

def _sanitize_string(value: str) -> str:
    """
    Sanitizes string values for safe use in filter expressions.
    Escapes double quotes to prevent injection.
    """
    if not isinstance(value, str):
        return str(value)
    # Escape double quotes
    return value.replace('"', '\\"').replace("\\", "\\\\")


def _build_filter(**kwargs) -> str:
    """
    Builds a Milvus boolean expression from keyword arguments (None values are ignored).
    Sanitizes all string values to prevent filter injection.
    """
    clauses = []

    if kwargs.get("gender"):
        clauses.append(f'gender == "{_sanitize_string(kwargs["gender"])}"')
    if kwargs.get("master_category"):
        clauses.append(f'master_category == "{_sanitize_string(kwargs["master_category"])}"')
    if kwargs.get("article_type"):
        clauses.append(f'article_type == "{_sanitize_string(kwargs["article_type"])}"')
    if kwargs.get("base_colour"):
        clauses.append(f'base_colour == "{_sanitize_string(kwargs["base_colour"])}"')
    if kwargs.get("season"):
        clauses.append(f'season == "{_sanitize_string(kwargs["season"])}"')
    if kwargs.get("usage"):
        clauses.append(f'usage == "{_sanitize_string(kwargs["usage"])}"')
    if kwargs.get("year"):
        year = int(kwargs["year"])
        clauses.append(f'year == {year}')
    if kwargs.get("has_image") is True:
        clauses.append("has_image == true")

    return " && ".join(clauses)


def _fuse_scores(
    hits_a: list[dict],
    hits_b: list[dict],
    weight_a: float = 0.5,
    top_k: int = 10,
    k: int = 60,
) -> list[dict]:
    """
    Reciprocal Rank Fusion of two ranked result lists.

    RRF formula: score(d) = sum(weight_i / (rank_i(d) + k))
    where rank is 1-based position in each list.

    Parameters
    ----------
    hits_a : list[dict]
        First ranked result list
    hits_b : list[dict]
        Second ranked result list
    weight_a : float
        Weight for the first list (weight_b = 1 - weight_a)
    top_k : int
        Number of top results to return
    k : int
        RRF smoothing constant (default 60)

    Returns
    -------
    list[dict]
        Top-k results with the highest fused scores
    """
    scores: dict[int, dict] = {}
    weight_b = 1.0 - weight_a

    # Process first list
    for rank, hit in enumerate(hits_a, start=1):
        doc_id = hit["id"]
        rrf = weight_a / (rank + k)
        if doc_id not in scores:
            scores[doc_id] = {"fused_score": 0.0, **hit}
        scores[doc_id]["fused_score"] += rrf

    # Process second list
    for rank, hit in enumerate(hits_b, start=1):
        doc_id = hit["id"]
        rrf = weight_b / (rank + k)
        if doc_id not in scores:
            scores[doc_id] = {"fused_score": 0.0, **hit}
        else:
            # Update with data from the second list if not already present
            for key, value in hit.items():
                if key not in scores[doc_id] or key == "id":
                    scores[doc_id][key] = value
        scores[doc_id]["fused_score"] += rrf

    ranked = sorted(scores.values(), key=lambda x: x["fused_score"], reverse=True)
    return ranked[:top_k]


def _to_search_result(row: dict) -> SearchResult:
    """Converts a raw dict from the repository into a SearchResult Pydantic model."""
    return SearchResult(
        id=row["id"],
        score=row.get("score", 0.0),
        product_name=row.get("product_name", ""),
        gender=row.get("gender", ""),
        master_category=row.get("master_category", ""),
        sub_category=row.get("sub_category", ""),
        article_type=row.get("article_type", ""),
        base_colour=row.get("base_colour", ""),
        season=row.get("season", ""),
        year=row.get("year", 0),
        usage=row.get("usage", ""),
        has_image=row.get("has_image", False),
        fused_score=row.get("fused_score"),
    )


class FashionService(IFashionService):
    """
    Implementation of IFashionService - uses FashionRepository for all I/O
    and CLIPEmbeddingService for encoding text and images.
    Equivalent to a Java @Service class that implements IFashionService.
    """

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def create_product(self, product: FashionProductCreate) -> dict:
        """Creates a new product with CLIP embeddings."""
        text_emb = embedding_service.encode_text_one(product.product_name)
        has_image = False
        image_emb = embedding_service.zero_vector()

        if product.image_url:
            try:
                image_emb = embedding_service.encode_from_url(product.image_url)
                has_image = True
            except Exception as e:
                logger.warning(f"Failed to encode image from URL: {e}")
                # Continue with zero vector

        record = {
            **product.model_dump(exclude={"image_url"}),
            "has_image": has_image,
            "text_embedding": text_emb,
            "image_embedding": image_emb,
        }
        result = fashion_repository.insert([record])
        return {
            "inserted_ids": result.get("ids", []),
            "insert_count": result.get("insert_count", 0),
        }

    def get_product(self, product_id: int) -> FashionProduct:
        """Fetches a product by ID."""
        if product_id <= 0:
            raise ValueError("Product ID must be positive")

        row = fashion_repository.find_by_id(product_id)
        if row is None:
            raise KeyError(f"Product {product_id} not found")
        return FashionProduct(**row)

    def get_product_with_vectors(self, product_id: int) -> dict:
        """Fetches a product with its embeddings."""
        if product_id <= 0:
            raise ValueError("Product ID must be positive")

        row = fashion_repository.find_by_id_with_vectors(product_id)
        if row is None:
            raise KeyError(f"Product {product_id} not found")
        return row

    def list_products(
        self,
        gender, master_category, article_type, base_colour,
        season, year, usage, has_image, limit, offset,
    ) -> list[FashionProduct]:
        """Lists products with optional filters."""
        if limit <= 0:
            raise ValueError("Limit must be positive")
        if offset < 0:
            raise ValueError("Offset cannot be negative")

        filter_expr = _build_filter(
            gender=gender, master_category=master_category, article_type=article_type,
            base_colour=base_colour, season=season, year=year, usage=usage,
            has_image=has_image,
        ) or "id >= 0"

        rows = fashion_repository.find_all(filter_expr, limit=limit, offset=offset)
        return [FashionProduct(**row) for row in rows]

    def update_product(self, product_id: int, update: FashionProductUpdate) -> dict:
        """Updates an existing product."""
        if product_id <= 0:
            raise ValueError("Product ID must be positive")

        record = fashion_repository.find_by_id_with_vectors(product_id)
        if record is None:
            raise KeyError(f"Product {product_id} not found")

        # Ensure primary key is present
        if "id" not in record:
            raise ValueError("Primary key 'id' missing from record")

        update_data = update.model_dump(exclude_none=True)
        image_url = update_data.pop("image_url", None)
        record.update(update_data)

        # Re-encode text embedding if product_name changed
        if "product_name" in update_data:
            record["text_embedding"] = embedding_service.encode_text_one(
                record["product_name"]
            )

        # Re-encode image embedding if a new URL was provided
        if image_url is not None:
            try:
                record["image_embedding"] = embedding_service.encode_from_url(image_url)
                record["has_image"] = True
            except Exception as e:
                logger.error(f"Failed to encode new image: {e}")
                raise ValueError(f"Failed to encode image from URL: {e}")

        result = fashion_repository.upsert(record)
        return {"upserted_count": result.get("upsert_count", 0)}

    def delete_product(self, product_id: int) -> dict:
        """Deletes a product by ID."""
        if product_id <= 0:
            raise ValueError("Product ID must be positive")

        result = fashion_repository.delete_by_id(product_id)
        return {"delete_count": result.get("delete_count", 0)}

    # ── Text search ───────────────────────────────────────────────────────────

    def text_search(self, query: str, top_k: int) -> list[SearchResult]:
        """Semantic text search."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        qvec = embedding_service.encode_text_one(query)
        hits = fashion_repository.search([qvec], "text_embedding", top_k=top_k)[0]
        return [_to_search_result(h) for h in hits]

    def filtered_text_search(
        self, query: str, filter_expr: str, top_k: int
    ) -> list[SearchResult]:
        """Text search with a filter."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        qvec = embedding_service.encode_text_one(query)
        hits = fashion_repository.search(
            [qvec], "text_embedding", top_k=top_k, filter_expr=filter_expr,
        )[0]
        return [_to_search_result(h) for h in hits]

    def colour_facet_search(
        self, query: str, base_colour: str, top_k: int
    ) -> list[SearchResult]:
        """Text search filtered by colour."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if not base_colour:
            raise ValueError("base_colour cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        filter_expr = f'base_colour == "{_sanitize_string(base_colour)}"'
        qvec = embedding_service.encode_text_one(query)
        hits = fashion_repository.search(
            [qvec], "text_embedding", top_k=top_k, filter_expr=filter_expr,
        )[0]
        return [_to_search_result(h) for h in hits]

    # ── Image search ──────────────────────────────────────────────────────────

    def image_search_by_url(
        self, url: str, top_k: int, images_only: bool
    ) -> list[SearchResult]:
        """Visual similarity search by image URL."""
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        qvec = embedding_service.encode_from_url(url)
        filter_expr = "has_image == true" if images_only else ""
        hits = fashion_repository.search(
            [qvec], "image_embedding", top_k=top_k, filter_expr=filter_expr,
        )[0]
        return [_to_search_result(h) for h in hits]

    def image_search_by_bytes(
        self, data: bytes, top_k: int, images_only: bool, filter_expr: str = "",
    ) -> list[SearchResult]:
        """Visual similarity search by raw image bytes."""
        if not data:
            raise ValueError("Image data cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        qvec = embedding_service.encode_from_bytes(data)
        parts = []
        if images_only:
            parts.append("has_image == true")
        if filter_expr:
            parts.append(filter_expr)
        combined = " && ".join(parts)

        hits = fashion_repository.search(
            [qvec], "image_embedding", top_k=top_k, filter_expr=combined,
        )[0]
        return [_to_search_result(h) for h in hits]

    def image_search_by_base64(self, b64: str, top_k: int) -> list[SearchResult]:
        """Visual similarity search by base64-encoded image."""
        if not b64 or not b64.strip():
            raise ValueError("Base64 string cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        qvec = embedding_service.encode_from_base64(b64)
        hits = fashion_repository.search(
            [qvec], "image_embedding", top_k=top_k,
        )[0]
        return [_to_search_result(h) for h in hits]

    # ── Cross-modal search ────────────────────────────────────────────────────

    def text_to_image_search(
        self, query: str, top_k: int, images_only: bool
    ) -> list[SearchResult]:
        """Cross-modal: encodes text -> searches image_embedding."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        qvec = embedding_service.encode_text_one(query)
        filter_expr = "has_image == true" if images_only else ""
        hits = fashion_repository.search(
            [qvec], "image_embedding", top_k=top_k, filter_expr=filter_expr,
        )[0]
        return [_to_search_result(h) for h in hits]

    def image_to_text_search(self, data: bytes, top_k: int) -> list[SearchResult]:
        """Reverse cross-modal: encodes image -> searches text_embedding."""
        if not data:
            raise ValueError("Image data cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        qvec = embedding_service.encode_from_bytes(data)
        hits = fashion_repository.search(
            [qvec], "text_embedding", top_k=top_k,
        )[0]
        return [_to_search_result(h) for h in hits]

    # ── Advanced search ───────────────────────────────────────────────────────

    def find_similar(
        self, product_id: int, text_weight: float, top_k: int
    ) -> dict:
        """
        Finds similar products using both embeddings with RRF fusion.
        Fetches the stored embeddings of the source product, runs two ANN searches,
        and merges them with a weighted RRF formula.
        """
        if product_id <= 0:
            raise ValueError("Product ID must be positive")
        if not 0.0 <= text_weight <= 1.0:
            raise ValueError("text_weight must be between 0.0 and 1.0")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        record = fashion_repository.find_by_id_with_vectors(product_id)
        if record is None:
            raise KeyError(f"Product {product_id} not found")

        text_emb  = record.get("text_embedding")
        image_emb = record.get("image_embedding")

        if not text_emb or not image_emb:
            raise ValueError("Product is missing one or both embedding vectors")

        recall_k = max(top_k * 3, 50)
        text_hits  = fashion_repository.search([text_emb],  "text_embedding",  top_k=recall_k)[0]
        image_hits = fashion_repository.search([image_emb], "image_embedding", top_k=recall_k)[0]

        # Remove the source product from results
        text_hits  = [h for h in text_hits  if h["id"] != product_id]
        image_hits = [h for h in image_hits if h["id"] != product_id]

        fused = _fuse_scores(text_hits, image_hits, weight_a=text_weight, top_k=top_k)

        return {
            "product_id":  product_id,
            "text_weight": text_weight,
            "results":     fused,
        }

    def two_stage_search(
        self,
        image_base64: str,
        text_rerank: str | None,
        recall_k: int,
        final_k: int,
        filter_expr: str,
    ) -> dict:
        """
        Two-stage retrieval pipeline:
        Stage 1 - visual recall (ANN on image_embedding, recall_k candidates)
        Stage 2 - exact text cosine reranking in Python
        """
        if not image_base64 or not image_base64.strip():
            raise ValueError("image_base64 cannot be empty")

        image_emb = embedding_service.encode_from_base64(image_base64)
        candidates = fashion_repository.search(
            [image_emb], "image_embedding",
            top_k=recall_k, filter_expr=filter_expr,
            include_vectors=bool(text_rerank),
        )[0]

        if text_rerank and candidates:
            text_emb = embedding_service.encode_text_one(text_rerank)
            text_vec = np.array(text_emb, dtype=np.float32)
            for hit in candidates:
                stored = hit.get("text_embedding")
                if stored:
                    cos = float(np.dot(text_vec, np.array(stored, dtype=np.float32)))
                    hit["rerank_score"] = round(cos, 4)
                else:
                    hit["rerank_score"] = 0.0
            candidates.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)

        return {
            "recall_k":    recall_k,
            "final_k":     final_k,
            "text_rerank": text_rerank,
            "results":     candidates[:final_k],
        }

    def multimodal_fusion_search(
        self,
        text_query: str,
        image_base64: str,
        text_weight: float,
        top_k: int,
        filter_expr: str,
    ) -> list[SearchResult]:
        """
        Full multimodal fusion: two ANN searches + RRF merging.
        text_weight controls the balance between text and visual components.
        """
        if not text_query or not text_query.strip():
            raise ValueError("text_query cannot be empty")
        if not image_base64 or not image_base64.strip():
            raise ValueError("image_base64 cannot be empty")
        if not 0.0 <= text_weight <= 1.0:
            raise ValueError("text_weight must be between 0.0 and 1.0")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        text_emb  = embedding_service.encode_text_one(text_query)
        image_emb = embedding_service.encode_from_base64(image_base64)

        recall_k = max(top_k * 3, 50)
        text_hits  = fashion_repository.search(
            [text_emb], "text_embedding", top_k=recall_k, filter_expr=filter_expr,
        )[0]
        image_hits = fashion_repository.search(
            [image_emb], "image_embedding", top_k=recall_k, filter_expr=filter_expr,
        )[0]

        fused = _fuse_scores(text_hits, image_hits, weight_a=text_weight, top_k=top_k)
        return [_to_search_result(h) for h in fused]

    def batch_text_search(self, queries: list[str], top_k: int) -> list[dict]:
        """
        Batch ANN search: encodes all queries at once and searches in a single
        Milvus search call. More efficient than N separate calls.
        """
        if not queries:
            raise ValueError("Queries list cannot be empty")
        if len(queries) > 10:
            raise ValueError("Maximum 10 queries per batch")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        query_vecs = embedding_service.encode_text(queries)
        raw = fashion_repository.search(query_vecs, "text_embedding", top_k=top_k)
        return [
            {"query": q, "results": [_to_search_result(h).model_dump() for h in hits]}
            for q, hits in zip(queries, raw)
        ]

    def year_range_search(
        self, query: str, from_year: int, to_year: int, top_k: int
    ) -> list[SearchResult]:
        """Text ANN search with a year range filter."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if from_year > to_year:
            raise ValueError("from_year must be <= to_year")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        filter_expr = f"year >= {from_year} && year <= {to_year}"
        qvec = embedding_service.encode_text_one(query)
        hits = fashion_repository.search(
            [qvec], "text_embedding", top_k=top_k, filter_expr=filter_expr,
        )[0]
        return [_to_search_result(h) for h in hits]

    # ── Collection management ─────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Returns collection statistics."""
        return fashion_repository.get_stats()

    def reset_collection(self) -> None:
        """Drops and recreates the collection. Use only for resetting the demo environment."""
        fashion_repository.reset()


fashion_service = FashionService()
