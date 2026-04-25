from pydantic import BaseModel, Field


class BookBase(BaseModel):
    goodreads_id: str | None = Field(default=None, min_length=1, max_length=32)
    isbn: str = Field(..., min_length=1, max_length=32)
    title: str = Field(..., min_length=1, max_length=512)
    author: str = Field(..., min_length=1, max_length=256)
    genre: str = Field(default="General", min_length=1, max_length=128)
    publisher: str = Field(..., min_length=1, max_length=256)
    year: int = Field(default=2000, ge=0, le=3000)
    language: str = Field(..., min_length=1, max_length=32)
    description: str = Field("", max_length=4000)
    coverImg: str | None = Field(default=None, min_length=1, max_length=2048)
    pages: int | None = Field(default=None, ge=0, le=100_000)
    has_image: bool = Field(default=False)
    keywords: list[str] = Field(default_factory=list)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    goodreads_id: str | None = Field(default=None, min_length=1, max_length=32)
    isbn: str | None = Field(default=None, min_length=1, max_length=32)
    title: str | None = Field(default=None, min_length=1, max_length=512)
    author: str | None = Field(default=None, min_length=1, max_length=256)
    genre: str | None = Field(default=None, min_length=1, max_length=128)
    publisher: str | None = Field(default=None, min_length=1, max_length=256)
    year: int | None = Field(default=None, ge=0, le=3000)
    language: str | None = Field(default=None, min_length=1, max_length=32)
    description: str | None = Field(default=None, max_length=4000)
    coverImg: str | None = Field(default=None, min_length=1, max_length=2048)
    pages: int | None = Field(default=None, ge=0, le=100_000)
    has_image: bool | None = None
    keywords: list[str] | None = None


class Book(BookBase):
    id: int


class BookSearchResult(Book):
    score: float
