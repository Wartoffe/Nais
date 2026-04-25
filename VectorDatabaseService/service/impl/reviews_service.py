from config import REVIEWS_DEFAULT_TOP_K
from model.book_review import BookReviewCreate, BookReviewUpdate
from repository.reviews_repository import reviews_repository
from service.i_reviews_service import IReviewsService
from services.minilm_embedding_service import minilm_service


def _sanitize_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _build_filter(
    isbn: str | None,
    min_rating: int | None,
    max_rating: int | None,
    user_type: str | None,
) -> str:
    if min_rating is not None and max_rating is not None and min_rating > max_rating:
        raise ValueError("min_rating must be <= max_rating")

    parts = []
    if isbn:
        parts.append(f'isbn == "{_sanitize_string(isbn)}"')
    if min_rating is not None:
        parts.append(f"rating >= {int(min_rating)}")
    if max_rating is not None:
        parts.append(f"rating <= {int(max_rating)}")
    if user_type:
        parts.append(f'user_type == "{_sanitize_string(user_type)}"')

    return " && ".join(parts)


class ReviewsService(IReviewsService):

    # CRUD
    def create_review(self, review: BookReviewCreate) -> dict:
        text = review.review_text.strip()
        date_added = (review.date_added or review.created_at or "").strip()[:64]
        created_at = (review.created_at or review.date_added or "").strip()[:64]
        record = {
            "review_id": review.review_id.strip()[:64],
            "isbn": review.isbn.strip()[:32],
            "book_id": (review.book_id or "").strip()[:64],
            "rating": int(review.rating),
            "date_added": date_added,
            "n_votes": int(review.n_votes or 0),
            "user_type": (review.user_type or "dataset").strip()[:32],
            "created_at": created_at,
            "review_text": text[:4000],
            "review_embedding": minilm_service.encode_one(text),
        }
        result = reviews_repository.insert([record])
        return {
            "inserted_ids": result.get("ids", []),
            "insert_count": result.get("insert_count", 0),
        }

    def batch_create(self, reviews: list[BookReviewCreate]) -> dict:
        if not reviews:
            raise ValueError("reviews list cannot be empty")
        if len(reviews) > 400:
            raise ValueError("maximum 400 reviews per batch")

        records = []
        texts = []
        for review in reviews:
            text = review.review_text.strip()
            date_added = (review.date_added or review.created_at or "").strip()[:64]
            created_at = (review.created_at or review.date_added or "").strip()[:64]
            records.append(
                {
                    "review_id": review.review_id.strip()[:64],
                    "isbn": review.isbn.strip()[:32],
                    "book_id": (review.book_id or "").strip()[:64],
                    "rating": int(review.rating),
                    "date_added": date_added,
                    "n_votes": int(review.n_votes or 0),
                    "user_type": (review.user_type or "dataset").strip()[:32],
                    "created_at": created_at,
                    "review_text": text[:4000],
                }
            )
            texts.append(text)

        embeddings = minilm_service.encode(texts)
        for record, emb in zip(records, embeddings):
            record["review_embedding"] = emb

        result = reviews_repository.insert(records)
        return {
            "inserted_ids": result.get("ids", []),
            "insert_count": result.get("insert_count", 0),
        }

    def get_review(self, review_id: int) -> dict:
        if review_id <= 0:
            raise ValueError("review_id must be positive")
        row = reviews_repository.find_by_id(review_id)
        if row is None:
            raise KeyError(f"Review {review_id} not found")
        return row

    def get_review_by_business_id(self, review_business_id: str) -> dict:
        if not review_business_id or not review_business_id.strip():
            raise ValueError("review_business_id cannot be empty")
        row = reviews_repository.find_by_review_id(review_business_id.strip())
        if row is None:
            raise KeyError(f"Review {review_business_id} not found")
        return row

    def list_reviews(
        self,
        isbn: str | None,
        min_rating: int | None,
        max_rating: int | None,
        user_type: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        if offset < 0:
            raise ValueError("offset cannot be negative")

        filter_expr = _build_filter(isbn, min_rating, max_rating, user_type)
        return reviews_repository.find_all(filter_expr=filter_expr, limit=limit, offset=offset)

    def update_review(self, review_id: int, update: BookReviewUpdate) -> dict:
        if review_id <= 0:
            raise ValueError("review_id must be positive")

        current = reviews_repository.find_by_id_for_update(review_id)
        if current is None:
            raise KeyError(f"Review {review_id} not found")

        update_data = update.model_dump(exclude_none=True)
        if not update_data:
            return {"upsert_count": 0, "ids": [review_id], "message": "No changes supplied"}

        merged = dict(current)
        merged.update(update_data)
        merged["id"] = review_id

        if "review_text" in update_data:
            merged["review_text"] = merged["review_text"].strip()[:4000]
            merged["review_embedding"] = minilm_service.encode_one(merged["review_text"])

        result = reviews_repository.upsert(merged)
        return {
            "upsert_count": result.get("upsert_count", 0),
            "ids": result.get("ids", []),
        }

    def delete_review(self, review_id: int) -> dict:
        if review_id <= 0:
            raise ValueError("review_id must be positive")
        result = reviews_repository.delete_by_id(review_id)
        return {
            "deleted_id": review_id,
            "delete_count": result.get("delete_count", 0),
        }

    # Search
    def semantic_search(
        self,
        query: str,
        top_k: int = REVIEWS_DEFAULT_TOP_K,
        isbn: str | None = None,
        min_rating: int | None = None,
        user_type: str | None = None,
    ) -> list[dict]:
        if not query or not query.strip():
            raise ValueError("query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        filter_expr = _build_filter(isbn, min_rating, None, user_type)
        qvec = minilm_service.encode_one(query.strip())
        return reviews_repository.search_semantic([qvec], top_k=top_k, filter_expr=filter_expr)[0]

    def search_with_nprobe(
        self,
        query: str,
        nprobe: int,
        top_k: int,
        isbn: str | None,
        min_rating: int | None,
        user_type: str | None,
    ) -> list[dict]:
        if not query or not query.strip():
            raise ValueError("query cannot be empty")
        if nprobe < 1:
            raise ValueError("nprobe must be >= 1")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        filter_expr = _build_filter(isbn, min_rating, None, user_type)
        qvec = minilm_service.encode_one(query.strip())
        return reviews_repository.search_with_custom_nprobe(
            [qvec],
            nprobe=nprobe,
            top_k=top_k,
            filter_expr=filter_expr,
        )[0]

    def get_stats(self) -> dict:
        return reviews_repository.get_stats()


reviews_service = ReviewsService()
