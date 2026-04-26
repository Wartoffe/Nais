"""
Service interface for the fashion_products collection.
"""

from abc import ABC, abstractmethod
from model.fashion_product import (
    FashionProduct,
    FashionProductCreate,
    FashionProductUpdate,
    SearchResult,
)


class IFashionService(ABC):
    """
    Abstract service interface for fashion product operations.

    Every public method is @abstractmethod - the concrete implementation
    lives in service/impl/fashion_service.py.
    """

    # ── CRUD ──────────────────────────────────────────────────────────────────

    @abstractmethod
    def create_product(self, product: FashionProductCreate) -> dict:
        """
        Creates a new product.
        Encodes product_name -> text_embedding and optionally image_url -> image_embedding.
        """
        ...

    @abstractmethod
    def get_product(self, product_id: int) -> FashionProduct:
        """Fetches a single product by Milvus ID. Raises KeyError if not found."""
        ...

    @abstractmethod
    def get_product_with_vectors(self, product_id: int) -> dict:
        """Fetches a product together with its text_embedding and image_embedding."""
        ...

    @abstractmethod
    def list_products(
        self,
        gender: str | None,
        master_category: str | None,
        article_type: str | None,
        base_colour: str | None,
        season: str | None,
        year: int | None,
        usage: str | None,
        has_image: bool | None,
        limit: int,
        offset: int,
    ) -> list[FashionProduct]:
        """Lists products with optional scalar filters."""
        ...

    @abstractmethod
    def update_product(self, product_id: int, update: FashionProductUpdate) -> dict:
        """
        Partial product update.
        Milvus has no in-place update - implementation fetches, merges, and upserts.
        Re-encodes embeddings if product_name or image_url changed.
        """
        ...

    @abstractmethod
    def delete_product(self, product_id: int) -> dict:
        """Deletes a product by Milvus ID."""
        ...

    # ── Text search ───────────────────────────────────────────────────────────

    @abstractmethod
    def text_search(self, query: str, top_k: int) -> list[SearchResult]:
        """
        Semantic ANN search: encodes text -> searches text_embedding.
        Finds products whose names are semantically similar to the query.
        """
        ...

    @abstractmethod
    def filtered_text_search(
        self, query: str, filter_expr: str, top_k: int
    ) -> list[SearchResult]:
        """
        Semantic search with a scalar pre-filter.
        Milvus applies the filter BEFORE ANN search - more efficient than post-filtering.
        """
        ...

    @abstractmethod
    def colour_facet_search(
        self, query: str, base_colour: str, top_k: int
    ) -> list[SearchResult]:
        """Text ANN search restricted to a single colour - simulates faceted search."""
        ...

    # ── Image search ──────────────────────────────────────────────────────────

    @abstractmethod
    def image_search_by_url(
        self, url: str, top_k: int, images_only: bool
    ) -> list[SearchResult]:
        """Visual similarity: downloads image from URL -> encodes -> searches image_embedding."""
        ...

    @abstractmethod
    def image_search_by_bytes(
        self, data: bytes, top_k: int, images_only: bool, filter_expr: str = ""
    ) -> list[SearchResult]:
        """
        Visual similarity: encodes uploaded image -> searches image_embedding.
        filter_expr is combined with the images_only filter (when set).
        """
        ...

    @abstractmethod
    def image_search_by_base64(self, b64: str, top_k: int) -> list[SearchResult]:
        """Visual similarity: decodes base64 image -> encodes -> searches image_embedding."""
        ...

    # ── Cross-modal search ────────────────────────────────────────────────────

    @abstractmethod
    def text_to_image_search(
        self, query: str, top_k: int, images_only: bool
    ) -> list[SearchResult]:
        """
        Cross-modal: encodes text -> searches image_embedding.
        Finds photos that visually match the text description.
        """
        ...

    @abstractmethod
    def image_to_text_search(self, data: bytes, top_k: int) -> list[SearchResult]:
        """
        Reverse cross-modal: encodes image -> searches text_embedding.
        Finds names that semantically describe the image content.
        """
        ...

    # ── Advanced search ───────────────────────────────────────────────────────

    @abstractmethod
    def find_similar(
        self, product_id: int, text_weight: float, top_k: int
    ) -> dict:
        """
        Finds similar products using both embeddings with RRF fusion.
        Fetches stored embeddings of the source product, runs two ANN searches,
        and merges them with a weighted RRF formula.
        """
        ...

    @abstractmethod
    def two_stage_search(
        self,
        image_base64: str,
        text_rerank: str | None,
        recall_k: int,
        final_k: int,
        filter_expr: str,
    ) -> dict:
        """
        Two-stage pipeline:
        Stage 1 - visual recall (ANN on image_embedding, recall_k candidates)
        Stage 2 - text reranking (exact dot-product in Python)
        """
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    def batch_text_search(self, queries: list[str], top_k: int) -> list[dict]:
        """Batch ANN search: multiple query vectors in a single network round-trip."""
        ...

    @abstractmethod
    def year_range_search(
        self, query: str, from_year: int, to_year: int, top_k: int
    ) -> list[SearchResult]:
        """Text ANN search with a year range filter."""
        ...

    # ── Collection management ─────────────────────────────────────────────────

    @abstractmethod
    def get_stats(self) -> dict:
        """Returns collection statistics (row_count, etc.)."""
        ...

    @abstractmethod
    def reset_collection(self) -> None:
        """Drops and recreates the collection. Use only for resetting the demo environment."""
        ...
