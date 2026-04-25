import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from service.impl.fashion_chat_service import fashion_chat_service
from service.impl.sciq_chat_service import sciq_chat_service
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
    "/api/v1/fashion-lab/chat",
    summary="Outfit recommendation — retrieves catalog items from Milvus, then asks LLM to compose an outfit",
    description=(
        "1. Encodes the message with CLIP → ANN search on fashion_lab (top-10).\n"
        "2. Builds a prompt with the retrieved items as context.\n"
        "3. Sends to Ollama (`qwen2.5:1.5b`) and returns the recommendation.\n\n"
        "Example: `{\"message\": \"What should I combine with a black t-shirt for a casual look?\"}`"
    ),
)
def fashion_chat(request: ChatRequest):
    try:
        return fashion_chat_service.chat(request.message)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error("Fashion chat error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/api/v1/sciq/chat",
    summary="Science Q&A — retrieves relevant passages from sciq_passages, then asks LLM to answer",
    description=(
        "1. Encodes the question with MiniLM → ANN search on sciq_passages (top-4).\n"
        "2. Builds a RAG prompt with the retrieved passages as context.\n"
        "3. Sends to Ollama (`qwen2.5:1.5b`) and returns the answer.\n\n"
        "Example: `{\"message\": \"Why do objects fall at the same speed regardless of mass?\"}`"
    ),
)
def sciq_chat(request: ChatRequest):
    try:
        return sciq_chat_service.chat(request.message)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error("SciQ chat error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
