from abc import ABC, abstractmethod
from typing import Optional

from model.fashion_product import FashionProductBase


class IFashionLabService(ABC):

    @abstractmethod
    def create_product(self, product: FashionProductBase) -> dict:
        """Encodes the product name with the CLIP text tower; image_embedding = zero vector."""
        ...

    @abstractmethod
    def list_products(
        self,
        gender: Optional[str],
        colour: Optional[str],
        category: Optional[str],
        limit: int,
        offset: int,
    ) -> list[dict]:
        """Pure scalar search - no vector ranking."""
        ...

    @abstractmethod
    def get_product(self, product_id: int) -> dict:
        """Fetches a single record by Milvus ID."""
        ...

    @abstractmethod
    def delete_product(self, product_id: int) -> dict:
        """Deletes a record by Milvus ID."""
        ...

    @abstractmethod
    def text_search(self, query: str, top_k: int) -> list[dict]:
        """ANN search: encodes text -> searches text_embedding."""
        ...

    @abstractmethod
    def filtered_search(
        self,
        query: str,
        gender: Optional[str],
        colour: Optional[str],
        category: Optional[str],
        top_k: int,
    ) -> list[dict]:
        """Pre-filtered ANN - scalar WHERE clause applied before ANN search."""
        ...

    @abstractmethod
    def image_search(self, url: str, top_k: int) -> list[dict]:
        """Downloads image from URL, encodes with CLIP image tower, searches image_embedding."""
        ...

    @abstractmethod
    def text_to_image_search(self, query: str, top_k: int) -> list[dict]:
        """CLIP shared space: text vector -> searches image_embedding."""
        ...

    @abstractmethod
    def image_to_text_search(self, url: str, top_k: int) -> list[dict]:
        """Reverse cross-modal: image vector -> searches text_embedding."""
        ...

    @abstractmethod
    def multimodal_search(
        self,
        text: str,
        image_url: str,
        text_weight: float,
        top_k: int,
    ) -> list[dict]:
        """Two independent ANN searches + Reciprocal Rank Fusion (RRF)."""
        ...

    @abstractmethod
    def search_paginated(self, query: str, page: int, page_size: int) -> dict:
        """ANN search with offset-based pagination."""
        ...

    @abstractmethod
    def search_with_iterator(self, query: str, batch_size: int) -> dict:
        """Iterative search through all results in batch steps."""
        ...

    @abstractmethod
    def grouped_search(self, query: str, group_by_field: str, group_size: int, top_k: int) -> list[dict]:
        """Grouped ANN search - max group_size results per value of group_by_field."""
        ...

    @abstractmethod
    def range_search(self, query: str, min_score: float, max_score: float) -> list[dict]:
        """Native Milvus range search - COSINE score within [min_score, max_score]."""
        ...

    @abstractmethod
    def search_with_consistency(self, query: str, consistency_level: str, top_k: int) -> list[dict]:
        """ANN search with an explicit consistency level."""
        ...

    @abstractmethod
    def hybrid_search_weighted(self, query: str, text_weight: float, top_k: int) -> list[dict]:
        """Hybrid search with WeightedRanker (alternative to RRFRanker)."""
        ...

    @abstractmethod
    def batch_text_search(self, queries: list[str], top_k: int) -> list[dict]:
        """Batch search - N queries in a single Milvus search() call."""
        ...

    @abstractmethod
    def search_template_filter(self, query: str, min_year: int, colors: list[str], top_k: int) -> dict:
        """Search with a parameterized filter expression."""
        ...

    @abstractmethod
    def search_in_partition(self, query: str, partition: str, top_k: int) -> dict:
        """ANN search restricted to a specified partition."""
        ...

    @abstractmethod
    def products_by_year_range(self, min_year: int, max_year: int, limit: int) -> list[dict]:
        """Range query: year >= min_year && year <= max_year."""
        ...

    @abstractmethod
    def products_by_name_pattern(self, pattern: str, limit: int) -> list[dict]:
        """LIKE search on the product_name field."""
        ...

    @abstractmethod
    def products_without_images(self, limit: int) -> list[dict]:
        """Returns products where has_image == false."""
        ...

    @abstractmethod
    def products_in_colors(self, colors: list[str], limit: int) -> list[dict]:
        """IN operator - returns products whose colour is in the provided list."""
        ...

    @abstractmethod
    def paginated_products(self, filter_expr: str, page: int, page_size: int) -> dict:
        """Offset-based result pagination."""
        ...

    @abstractmethod
    def advanced_filtered_search(
        self,
        query: str,
        genders: list[str] | None,
        seasons: list[str] | None,
        colours: list[str] | None,
        min_year: int | None,
        exclude_type: str | None,
        top_k: int,
    ) -> dict:
        """ANN search with a complex boolean filter (IN, AND, >=, !=)."""
        ...

    @abstractmethod
    def search_by_threshold(self, query: str, min_score: float, top_k: int) -> list[dict]:
        """ANN search with a post-filter on minimum COSINE score threshold."""
        ...

    @abstractmethod
    def get_random_sample(self, sample_size: int) -> list[dict]:
        """Random sample from the collection."""
        ...

    @abstractmethod
    def count_by_category(self, category: str) -> dict:
        """COUNT(*) aggregation by master_category."""
        ...

    @abstractmethod
    def get_facets(self) -> dict:
        """Faceted aggregation - occurrence counts per categorical field."""
        ...

    @abstractmethod
    def create_products_batch(self, products: list) -> dict:
        """Batch insert of multiple products - encoding and insert in a single call."""
        ...

    @abstractmethod
    def hybrid_text_search(self, query: str, top_k: int) -> list[dict]:
        """Milvus hybrid_search - simultaneous search on text_embedding and image_embedding."""
        ...

    @abstractmethod
    def search_with_tuning(self, query: str, nprobe: int, top_k: int) -> list[dict]:
        """Search with an explicit nprobe parameter for IVF_FLAT tuning demo."""
        ...

    @abstractmethod
    def image_search_from_pil(self, img, top_k: int) -> list[dict]:
        """Image search, accepts a PIL object instead of a URL."""
        ...

    @abstractmethod
    def image_to_text_search_from_pil(self, img, top_k: int) -> list[dict]:
        """Cross-modal image-to-text, accepts a PIL object instead of a URL."""
        ...

    @abstractmethod
    def multimodal_search_from_pil(self, text: str, img, text_weight: float, top_k: int) -> list[dict]:
        """Multimodal fusion, accepts a PIL object instead of a URL."""
        ...

    @abstractmethod
    def get_stats(self) -> dict:
        """Returns collection statistics for fashion_lab."""
        ...
