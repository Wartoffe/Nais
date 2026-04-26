from abc import ABC, abstractmethod

from model.sciq_document import SciQDocumentCreate, SciQRagRequest, SciQRagResult


class ISciQService(ABC):

    # ── CRUD ─────────────────────────────────────────────────────────────────

    @abstractmethod
    def create_document(self, doc: SciQDocumentCreate) -> dict:
        pass

    @abstractmethod
    def batch_create(self, docs: list[SciQDocumentCreate]) -> dict:
        pass

    @abstractmethod
    def get_document(self, doc_id: int) -> dict:
        pass

    @abstractmethod
    def list_documents(self, min_length: int | None, max_length: int | None, limit: int, offset: int) -> list[dict]:
        pass

    @abstractmethod
    def delete_document(self, doc_id: int) -> dict:
        pass

    @abstractmethod
    def batch_delete(self, entity_ids: list[int]) -> dict:
        pass

    # ── Search ────────────────────────────────────────────────────────────────

    @abstractmethod
    def semantic_search(self, query: str, top_k: int) -> list[dict]:
        pass

    @abstractmethod
    def keyword_search(self, query: str, top_k: int) -> list[dict]:
        pass

    @abstractmethod
    def hybrid_search(self, query: str, top_k: int) -> list[dict]:
        pass

    @abstractmethod
    def filtered_search(self, query: str, min_length: int | None, max_length: int | None, top_k: int) -> list[dict]:
        pass

    @abstractmethod
    def text_match_search(self, query: str, match_text: str, top_k: int) -> list[dict]:
        pass

    @abstractmethod
    def search_by_length_range(self, query: str, min_length: int, max_length: int, top_k: int) -> list[dict]:
        pass

    @abstractmethod
    def search_by_doc_ids(self, query: str, doc_ids: list[int], top_k: int) -> list[dict]:
        pass

    @abstractmethod
    def search_with_metrics(self, query: str, top_k: int) -> dict:
        pass

    @abstractmethod
    def search_with_nprobe(self, query: str, nprobe: int, top_k: int) -> list[dict]:
        pass

    # ── RAG ───────────────────────────────────────────────────────────────────

    @abstractmethod
    def rag_query(self, request: SciQRagRequest) -> SciQRagResult:
        pass

    # ── Stats ─────────────────────────────────────────────────────────────────

    @abstractmethod
    def get_stats(self) -> dict:
        pass
