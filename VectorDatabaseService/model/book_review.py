from pydantic import BaseModel, Field


class BookReviewBase(BaseModel):
    review_id: str = Field(..., min_length=1, max_length=64)
    isbn: str = Field(..., min_length=1, max_length=32)
    book_id: str | None = Field(default=None, min_length=1, max_length=64)
    rating: int = Field(..., ge=1, le=5)
    date_added: str | None = Field(default=None, min_length=1, max_length=64)
    n_votes: int = Field(default=0, ge=0, le=1_000_000)
    user_type: str | None = Field(default=None, min_length=1, max_length=32)
    created_at: str | None = Field(default=None, min_length=1, max_length=64)
    review_text: str = Field(..., min_length=1, max_length=4000)


class BookReviewCreate(BookReviewBase):
    pass


class BookReviewUpdate(BaseModel):
    book_id: str | None = Field(default=None, min_length=1, max_length=64)
    rating: int | None = Field(default=None, ge=1, le=5)
    date_added: str | None = Field(default=None, min_length=1, max_length=64)
    n_votes: int | None = Field(default=None, ge=0, le=1_000_000)
    user_type: str | None = Field(default=None, min_length=1, max_length=32)
    created_at: str | None = Field(default=None, min_length=1, max_length=64)
    review_text: str | None = Field(default=None, min_length=1, max_length=4000)


class BookReview(BookReviewBase):
    id: int


class BookReviewSearchResult(BookReview):
    score: float
