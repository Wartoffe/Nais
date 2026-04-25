import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from service.impl.books_chat_service import books_chat_service
from config import OLLAMA_MODEL

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Books AI Chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


@router.post(
    "/api/v1/books/chat",
    summary="Book discovery — retrieves catalog items from Milvus, then asks LLM to recommend",
    description=(
        "1. Encodes the message with MiniLM → ANN search on books (top-5).\n"
        "2. Builds a RAG prompt with the retrieved books as context.\n"
        f"3. Sends to Ollama (`{OLLAMA_MODEL}`) and returns the recommendation.\n\n"
        "Example: `{\"message\": \"Looking for a sci-fi novel about space exploration\"}`"
    ),
)
def books_chat(request: ChatRequest):
    try:
        return books_chat_service.chat(request.message)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error("Books chat error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/api/v1/books/reviews/chat",
    summary="Review sentiment — retrieves reader reviews from Milvus, then asks LLM to summarise opinions",
    description=(
        "1. Encodes the question with MiniLM → ANN search on book_reviews (top-6).\n"
        "2. Builds a RAG prompt with the retrieved reviews as context.\n"
        f"3. Sends to Ollama (`{OLLAMA_MODEL}`) and returns a sentiment summary.\n\n"
        "Example: `{\"message\": \"What do readers think about books by Ursula K. Le Guin?\"}`"
    ),
)
def reviews_chat(request: ChatRequest):
    try:
        return books_chat_service.reviews_chat(request.message)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error("Reviews chat error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
