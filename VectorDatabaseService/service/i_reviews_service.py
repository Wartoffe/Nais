from abc import ABC, abstractmethod

from model.book_review import BookReviewCreate, BookReviewUpdate


class IReviewsService(ABC):

    @abstractmethod
    def create_review(self, review: BookReviewCreate) -> dict:
        pass

    @abstractmethod
    def batch_create(self, reviews: list[BookReviewCreate]) -> dict:
        pass

    @abstractmethod
    def get_review(self, review_id: int) -> dict:
        pass

    @abstractmethod
    def get_review_by_business_id(self, review_business_id: str) -> dict:
        pass

    @abstractmethod
    def list_reviews(
        self,
        isbn: str | None,
        min_rating: int | None,
        max_rating: int | None,
        user_type: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        pass

    @abstractmethod
    def update_review(self, review_id: int, update: BookReviewUpdate) -> dict:
        pass

    @abstractmethod
    def delete_review(self, review_id: int) -> dict:
        pass

    @abstractmethod
    def semantic_search(
        self,
        query: str,
        top_k: int,
        isbn: str | None,
        min_rating: int | None,
        user_type: str | None,
    ) -> list[dict]:
        pass

    @abstractmethod
    def search_with_nprobe(
        self,
        query: str,
        nprobe: int,
        top_k: int,
        isbn: str | None,
        min_rating: int | None,
        user_type: str | None,
    ) -> list[dict]:
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        pass
