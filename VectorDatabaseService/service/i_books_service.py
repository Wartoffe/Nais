from abc import ABC, abstractmethod

from model.book import BookCreate, BookUpdate


class IBooksService(ABC):

    @abstractmethod
    def create_book(self, book: BookCreate) -> dict:
        pass

    @abstractmethod
    def batch_create(self, books: list[BookCreate]) -> dict:
        pass

    @abstractmethod
    def get_book(self, book_id: int) -> dict:
        pass

    @abstractmethod
    def get_book_by_isbn(self, isbn: str) -> dict:
        pass

    @abstractmethod
    def list_books(
        self,
        genre: str | None,
        language: str | None,
        year_from: int | None,
        year_to: int | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        pass

    @abstractmethod
    def update_book(self, book_id: int, update: BookUpdate) -> dict:
        pass

    @abstractmethod
    def delete_book(self, book_id: int) -> dict:
        pass

    @abstractmethod
    def semantic_search(self, query: str, top_k: int) -> list[dict]:
        pass

    @abstractmethod
    def filtered_search(
        self,
        query: str,
        genre: str | None,
        language: str | None,
        year_from: int | None,
        year_to: int | None,
        top_k: int,
    ) -> list[dict]:
        pass

    @abstractmethod
    def iterator_search(
        self,
        query: str,
        genre: str | None,
        language: str | None,
        year_from: int | None,
        year_to: int | None,
        batch_size: int,
        max_items: int,
    ) -> dict:
        pass

    @abstractmethod
    def keyword_search(self, query: str, top_k: int) -> list[dict]:
        pass

    @abstractmethod
    def hybrid_search(
        self,
        query: str,
        top_k: int,
        genre: str | None,
        language: str | None,
        year_from: int | None,
        year_to: int | None,
    ) -> list[dict]:
        pass

    @abstractmethod
    def search_with_nprobe(self, query: str, nprobe: int, top_k: int) -> list[dict]:
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        pass
