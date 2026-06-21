import logging

from config import BOOKS_TOP_K
from service.impl.books_service import books_service
from services.llm_service import llm_service
from services.embedding_service import embedding_service
from services.redis_cache_service import redis_cache

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

        # 1. Tačna cache provera
        cached = redis_cache.get_exact(message)
        if cached:
            cached["cache_hit"] = "exact"
            return cached
        
        # 2. Generiši embedding
        try:
            query_embedding = embedding_service.encode_text_one(message)
        except Exception as exc:
            logger.warning("Embedding generacija neuspešna: %s — preskačem semantic keš", exc)
            query_embedding = None
 
        # 3. Semantic cache provjera
        if query_embedding:
            cached = redis_cache.get_semantic(query_embedding)
            if cached:
                cached["cache_hit"] = "semantic"
                return cached

        # 4. Milvus pretraga
        hits = books_service.semantic_search(message, effective_top_k)

        if not hits:
            return {
                "response": "Nisam pronašao dovoljno relevantnih knjiga za ovo pitanje.",
                "context_books": [],
                "cache_hit": "miss",
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

        # 5. Ollama generisanje 
        response = llm_service.chat(_SYSTEM_PROMPT, user_prompt)
        response_data = {
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
            "cache_hit": "miss",
        }

        # 6. Upis u keš
        cache_payload = {k: v for k, v in response_data.items() if k != "cache_hit"}
        redis_cache.set_exact(message, cache_payload)
        if query_embedding:
            redis_cache.set_semantic(message, query_embedding, cache_payload)
 
        return response_data


books_chat_service = BooksChatService()
