import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from service.impl.books_chat_service import books_chat_service
from service.impl.reviews_chat_service import reviews_chat_service
from services.llm_service import llm_service
from config import OLLAMA_MODEL

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


@router.get("/api/v1/chat/health", summary="Check if Ollama LLM is reachable")
def chat_health():
    available = llm_service.is_available()
    return {"ollama_available": available, "model": OLLAMA_MODEL}


@router.post(
    "/api/v1/books/chat",
    summary="Books assistant — retrieves top-k books and asks Ollama to answer with book context",
    description=(
        "1. Encodes the message with the books text encoder (CLIP) and runs ANN search on description_embedding.\n"
        "2. Builds a prompt with title, author, and description from top-k books.\n"
        "3. Sends to Ollama and returns the answer/recommendation."
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
    "/api/v1/reviews/chat",
    summary="Reviews assistant — hybrid retrieval (dense + BM25) then Ollama answer",
    description=(
        "1. Runs hybrid retrieval on reviews (review_embedding + sparse_bm25).\n"
        "2. Builds a prompt with top-k review excerpts as context.\n"
        "3. Sends to Ollama and returns the answer."
    ),
)
def reviews_chat(request: ChatRequest):
    try:
        return reviews_chat_service.chat(request.message)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error("Reviews chat error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
