from pydantic import BaseModel, Field


class SciQDocumentBase(BaseModel):
    """
    Base schema for SciQ dataset documents containing core text fields.
    Includes support text, the question, and the correct answer.
    """
    support_text:   str = Field(..., min_length=1, max_length=1999)
    question:       str = Field(..., min_length=1, max_length=999)
    correct_answer: str = Field(..., min_length=1, max_length=499)


class SciQDocumentCreate(SciQDocumentBase):
    """Schema for creating a new SciQ document entry."""
    pass


class SciQDocument(SciQDocumentBase):
    """
    Complete SciQ document schema as stored in the database.
    Includes unique identifiers and metadata for the support text.
    """
    id:             int
    doc_id:         int
    support_length: int


class SciQSearchResult(SciQDocument):
    """Extends SciQDocument to include the similarity score from vector search."""
    score: float


class SciQRagRequest(BaseModel):
    """
    Schema for RAG (Retrieval-Augmented Generation) queries.
    Defines the question, search depth (top_k), and optional ground truth answer.
    """
    question:       str   = Field(..., min_length=1, max_length=999)
    top_k:          int   = Field(default=3, ge=1, le=20)
    correct_answer: str | None = Field(default=None)


class SciQRagResult(BaseModel):
    """
    Schema for the final RAG output.
    Contains the original query, retrieved context, and evaluation metrics like recall.
    """
    question:           str
    top_k:              int
    retrieved_passages: list[SciQSearchResult]
    context:            str
    recall_hit:         bool | None = None
    correct_answer:     str | None = None
