import logging

from config import BOOKS_TOP_K
from service.impl.books_service import books_service
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a helpful library assistant.
You answer user questions using only the provided book context.

Rules:
- Prefer recommending books that are clearly relevant to the question.
- Mention exact titles and authors from the context when possible.
- If context is insufficient, say you do not have enough information from the provided books.
- Keep the answer concise (under 220 words).
"""


class BooksChatService:
    def chat(self, message: str, top_k: int = 6) -> dict:
        effective_top_k = max(1, min(top_k, BOOKS_TOP_K))
        hits = books_service.semantic_search(message, effective_top_k)

        if not hits:
            return {
                "response": "Nisam pronašao dovoljno relevantnih knjiga za ovo pitanje.",
                "context_books": [],
            }

        context_lines = []
        for idx, hit in enumerate(hits, start=1):
            description = (hit.description or "").replace("\n", " ").strip()
            if len(description) > 700:
                description = f"{description[:700]}..."
            context_lines.append(
                f"[Book {idx}] Title: {hit.title} | Author: {hit.author} | Description: {description}"
            )

        user_prompt = (
            f"Retrieved books:\n{chr(10).join(context_lines)}\n\n"
            f"User question: {message}\n\n"
            "Please answer the question using only the retrieved books above."
        )

        response = llm_service.chat(_SYSTEM_PROMPT, user_prompt)
        return {
            "response": response,
            "context_books": [
                {
                    "id": hit.id,
                    "title": hit.title,
                    "author": hit.author,
                    "score": hit.score,
                }
                for hit in hits
            ],
        }


books_chat_service = BooksChatService()
