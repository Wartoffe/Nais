"""Service layer for the books domain.

Implements IBooksService. All business logic (validation, field cleaning,
synthetic-document construction, embedding) lives here. The repository
layer is responsible only for Milvus I/O.

Synthetic-document strategy
---------------------------
Every book is represented as a single prose string that concatenates all
searchable text fields.  The same string is stored in two places:
  - ``synthetic_document``  → tokenised by Milvus BM25 function → sparse vector
  - ``dense_embedding``     → encoded by MiniLM               → dense vector

This means both retrieval modes (keyword and semantic) operate over
identical text, guaranteeing consistent hybrid-search results.
"""

import logging

from config import BOOKS_DEFAULT_TOP_K
from model.book import BookCreate, BookUpdate
from repository.books_repository import books_repository
from service.i_books_service import IBooksService
from services.minilm_embedding_service import minilm_service

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
#  Helpers                                                                      #
# --------------------------------------------------------------------------- #

_SANITIZE = str.maketrans({"\\": "\\\\", '"': '\\"'})


def _s(value: str) -> str:
    return value.translate(_SANITIZE)


def _keywords_to_text(keywords: list[str] | None) -> str:
    if not keywords:
        return ""
    cleaned = [k.strip() for k in keywords if isinstance(k, str) and k.strip()]
    return ", ".join(cleaned)[:1024]


def _keywords_from_text(keywords_text: str) -> list[str]:
    if not keywords_text:
        return []
    return [k.strip() for k in keywords_text.split(",") if k.strip()]


def _build_synthetic_document(record: dict) -> str:
    """Build the single text that feeds BOTH dense embedding and BM25.

    Concatenates every searchable field so that keyword search on genre,
    author, or publisher and semantic search on description all hit the
    same vector space.
    """
    return (
        f"Goodreads ID: {record.get('goodreads_id', '')}. "
        f"Title: {record.get('title', '')}. "
        f"Author: {record.get('author', '')}. "
        f"Pages: {record.get('pages', '')}. "
        f"Genre: {record.get('genre', '')}. "
        f"Publisher: {record.get('publisher', '')}. "
        f"Year: {record.get('year', '')}. "
        f"Language: {record.get('language', '')}. "
        f"Description: {record.get('description', '')}. "
        f"Keywords: {record.get('keywords_text', '')}."
    )[:6000]


def _build_filter(
    genre: str | None,
    language: str | None,
    year_from: int | None,
    year_to: int | None,
) -> str:
    if year_from is not None and year_to is not None and year_from > year_to:
        raise ValueError("year_from must be <= year_to")

    parts = []
    if genre:
        parts.append(f'genre == "{_s(genre)}"')
    if language:
        parts.append(f'language == "{_s(language)}"')
    if year_from is not None:
        parts.append(f"year >= {int(year_from)}")
    if year_to is not None:
        parts.append(f"year <= {int(year_to)}")

    return " && ".join(parts)


def _to_output(row: dict) -> dict:
    """Deserialise keywords_text back to a list before returning to the API."""
    if not row:
        return row
    out = dict(row)
    out["keywords"] = _keywords_from_text(out.pop("keywords_text", ""))
    return out


# --------------------------------------------------------------------------- #
#  Service                                                                      #
# --------------------------------------------------------------------------- #

class BooksService(IBooksService):

    # ------------------------------------------------------------------ #
    #  CRUD                                                                #
    # ------------------------------------------------------------------ #

    def create_book(self, book: BookCreate) -> dict:
        keywords_text = _keywords_to_text(book.keywords)
        record = {
            "goodreads_id": (book.goodreads_id or "").strip()[:32],
            "isbn":         book.isbn.strip()[:32],
            "title":        book.title.strip()[:512],
            "author":       book.author.strip()[:256],
            "coverImg":     (book.coverImg or "").strip()[:2048],
            "pages":        int(book.pages or 0),
            "has_image":    bool(book.has_image),
            "genre":        book.genre.strip()[:128],
            "publisher":    book.publisher.strip()[:256],
            "year":         int(book.year),
            "language":     book.language.strip()[:32],
            "description":  book.description.strip()[:4000],
            "keywords_text": keywords_text,
        }

        # ── Synthetic document ───────────────────────────────────────────
        # Built once; stored as-is for BM25 and encoded for dense search.
        synth = _build_synthetic_document(record)
        record["synthetic_document"] = synth          # → BM25 sparse vector
        record["dense_embedding"] = minilm_service.encode_one(synth)  # → COSINE ANN

        result = books_repository.insert([record])
        return {
            "inserted_ids": result.get("ids", []),
            "insert_count": result.get("insert_count", 0),
        }

    def batch_create(self, books: list[BookCreate]) -> dict:
        if not books:
            raise ValueError("books list cannot be empty")
        if len(books) > 200:
            raise ValueError("maximum 200 books per batch")

        records, synth_docs = [], []
        for book in books:
            keywords_text = _keywords_to_text(book.keywords)
            record = {
                "goodreads_id":  (book.goodreads_id or "").strip()[:32],
                "isbn":          book.isbn.strip()[:32],
                "title":         book.title.strip()[:512],
                "author":        book.author.strip()[:256],
                "coverImg":      (book.coverImg or "").strip()[:2048],
                "pages":         int(book.pages or 0),
                "has_image":     bool(book.has_image),
                "genre":         book.genre.strip()[:128],
                "publisher":     book.publisher.strip()[:256],
                "year":          int(book.year),
                "language":      book.language.strip()[:32],
                "description":   book.description.strip()[:4000],
                "keywords_text": keywords_text,
            }
            synth = _build_synthetic_document(record)
            record["synthetic_document"] = synth      # → BM25
            synth_docs.append(synth)
            records.append(record)

        # Batch encode all synthetic documents in one shot (faster than one-by-one).
        embeddings = minilm_service.encode(synth_docs)  # → dense
        for record, emb in zip(records, embeddings):
            record["dense_embedding"] = emb

        result = books_repository.insert(records)
        return {
            "inserted_ids": result.get("ids", []),
            "insert_count": result.get("insert_count", 0),
        }

    def get_book(self, book_id: int) -> dict:
        """Simple query — dohvat po Milvus ID."""
        if book_id <= 0:
            raise ValueError("book_id must be positive")
        row = books_repository.find_by_id(book_id)
        if row is None:
            raise KeyError(f"Book {book_id} not found")
        return _to_output(row)

    def get_book_by_isbn(self, isbn: str) -> dict:
        """Simple query — dohvat po ISBN."""
        if not isbn or not isbn.strip():
            raise ValueError("isbn cannot be empty")
        row = books_repository.find_by_isbn(isbn.strip())
        if row is None:
            raise KeyError(f"Book with ISBN '{isbn}' not found")
        return _to_output(row)

    def list_books(
        self,
        genre: str | None,
        language: str | None,
        year_from: int | None,
        year_to: int | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        if offset < 0:
            raise ValueError("offset cannot be negative")
        filter_expr = _build_filter(genre, language, year_from, year_to)
        rows = books_repository.find_all(filter_expr=filter_expr, limit=limit, offset=offset)
        return [_to_output(r) for r in rows]

    def update_book(self, book_id: int, update: BookUpdate) -> dict:
        if book_id <= 0:
            raise ValueError("book_id must be positive")

        current = books_repository.find_by_id_for_update(book_id)
        if current is None:
            raise KeyError(f"Book {book_id} not found")

        update_data = update.model_dump(exclude_none=True)
        if not update_data:
            return {"upsert_count": 0, "ids": [book_id], "message": "No changes supplied"}

        cleaned = dict(update_data)
        if "keywords" in cleaned:
            cleaned["keywords_text"] = _keywords_to_text(cleaned.pop("keywords"))

        merged = dict(current)
        merged.update(cleaned)
        merged["id"] = book_id

        # Re-build synthetic document and re-encode only when a text field changed.
        text_fields = {"goodreads_id", "title", "author", "pages", "genre", "publisher", "year",
                       "language", "description", "keywords_text"}
        if text_fields & cleaned.keys():
            synth = _build_synthetic_document(merged)
            merged["synthetic_document"] = synth          # → BM25
            merged["dense_embedding"] = minilm_service.encode_one(synth)  # → dense

        result = books_repository.upsert(merged)
        return {
            "upsert_count": result.get("upsert_count", 0),
            "ids": result.get("ids", []),
        }

    def delete_book(self, book_id: int) -> dict:
        if book_id <= 0:
            raise ValueError("book_id must be positive")
        result = books_repository.delete_by_id(book_id)
        return {"deleted_id": book_id, "delete_count": result.get("delete_count", 0)}

    # ------------------------------------------------------------------ #
    #  Search — simple                                                     #
    # ------------------------------------------------------------------ #

    def semantic_search(self, query: str, top_k: int = BOOKS_DEFAULT_TOP_K) -> list[dict]:
        """Simple query — single-vector ANN po opisu knjige (dense cosine)."""
        if not query or not query.strip():
            raise ValueError("query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        qvec = minilm_service.encode_one(query.strip())
        rows = books_repository.search_dense([qvec], top_k=top_k)[0]
        return [_to_output(r) for r in rows]

    def keyword_search(self, query: str, top_k: int = BOOKS_DEFAULT_TOP_K) -> list[dict]:
        """BM25 sparse search over synthetic_document."""
        if not query or not query.strip():
            raise ValueError("query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        rows = books_repository.keyword_search(query.strip(), top_k=top_k)
        return [_to_output(r) for r in rows]

    # ------------------------------------------------------------------ #
    #  Search — complex                                                    #
    # ------------------------------------------------------------------ #

    def filtered_search(
        self,
        query: str,
        genre: str | None,
        language: str | None,
        year_from: int | None,
        year_to: int | None,
        top_k: int,
    ) -> list[dict]:
        """Complex query — vector + filter sa 2 uslova (npr. genre && year).

        Builds a Milvus boolean expression from any combination of
        genre, language, year_from, year_to and applies it as a pre-filter
        before ANN so the ANN candidate set is already restricted.
        """
        if not query or not query.strip():
            raise ValueError("query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        filter_expr = _build_filter(genre, language, year_from, year_to)
        qvec = minilm_service.encode_one(query.strip())
        rows = books_repository.search_dense([qvec], top_k=top_k, filter_expr=filter_expr)[0]
        return [_to_output(r) for r in rows]

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
        """Complex query — vector + filter sa iteratorom.

        Streams ANN results in pages of ``batch_size`` until ``max_items``
        is reached or the collection is exhausted.  Useful when top_k > 50
        (Milvus' per-call limit) or when the caller needs scroll-style access.

        Implementation uses search_dense_with_offset so we stay inside
        the standard search API — no iterator object to manage client-side.
        """
        if not query or not query.strip():
            raise ValueError("query cannot be empty")
        if not (1 <= batch_size <= 100):
            raise ValueError("batch_size must be between 1 and 100")
        if not (1 <= max_items <= 1000):
            raise ValueError("max_items must be between 1 and 1000")

        filter_expr = _build_filter(genre, language, year_from, year_to)
        qvec = minilm_service.encode_one(query.strip())

        results, offset = [], 0
        while len(results) < max_items:
            need = min(batch_size, max_items - len(results))
            batch = books_repository.search_dense_with_offset(
                [qvec],
                top_k=need,
                offset=offset,
                filter_expr=filter_expr,
            )[0]
            if not batch:
                break
            results.extend(batch)
            offset += len(batch)
            if len(batch) < need:          # collection exhausted
                break

        return {
            "query":       query,
            "filter_expr": filter_expr,
            "batch_size":  batch_size,
            "total":       len(results),
            "results":     [_to_output(r) for r in results],
        }

    def hybrid_search(
        self,
        query: str,
        top_k: int,
        genre: str | None,
        language: str | None,
        year_from: int | None,
        year_to: int | None,
    ) -> list[dict]:
        """Complex query — hybrid dense + BM25 (RRF fusion).

        Sends two AnnSearchRequests to Milvus hybrid_search:
          1. dense_embedding  — MiniLM cosine ANN
          2. sparse           — BM25 over synthetic_document

        Results are fused with Reciprocal Rank Fusion (RRFRanker).
        Optional metadata filter is applied to both legs simultaneously
        so post-fusion ranking is consistent.
        """
        if not query or not query.strip():
            raise ValueError("query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        filter_expr = _build_filter(genre, language, year_from, year_to)
        qvec = minilm_service.encode_one(query.strip())
        rows = books_repository.hybrid_search(
            query_text=query.strip(),
            query_vector=qvec,
            top_k=top_k,
            filter_expr=filter_expr,
        )
        return [_to_output(r) for r in rows]

    def search_with_nprobe(self, query: str, nprobe: int, top_k: int) -> list[dict]:
        """Dense ANN with caller-controlled nprobe for tuning comparison."""
        if not query or not query.strip():
            raise ValueError("query cannot be empty")
        if nprobe < 1:
            raise ValueError("nprobe must be >= 1")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        qvec = minilm_service.encode_one(query.strip())
        rows = books_repository.search_with_custom_nprobe([qvec], nprobe=nprobe, top_k=top_k)[0]
        return [_to_output(r) for r in rows]

    # ------------------------------------------------------------------ #
    #  Util                                                                #
    # ------------------------------------------------------------------ #

    def get_stats(self) -> dict:
        return books_repository.get_stats()


books_service = BooksService()