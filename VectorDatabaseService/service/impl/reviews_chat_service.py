import logging

from config import REVIEWS_TOP_K
from service.impl.reviews_service import reviews_service
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a helpful assistant for book review analysis.
You answer using only provided review excerpts retrieved from the review database.

Rules:
- Base the answer only on the given review context.
- Highlight patterns in sentiment, quality, strengths, and weaknesses when relevant.
- If context is insufficient, say you do not have enough information from the provided reviews.
- Keep the answer concise (under 220 words).
"""


class ReviewsChatService:
    def chat(self, message: str, top_k: int = 6) -> dict:
        effective_top_k = max(1, min(top_k, REVIEWS_TOP_K))
        hits = reviews_service.hybrid_search(message, effective_top_k)

        if not hits:
            return {
                "response": "Nisam pronašao dovoljno relevantnih recenzija za ovo pitanje.",
                "context_reviews": [],
            }

        context_lines = []
        for idx, hit in enumerate(hits, start=1):
            review_text = (hit.review_text or "").replace("\n", " ").strip()
            if len(review_text) > 700:
                review_text = f"{review_text[:700]}..."
            context_lines.append(
                (
                    f"[Review {idx}] ReviewID: {hit.review_id} | ISBN: {hit.isbn} | "
                    f"Rating: {hit.rating} | Votes: {hit.n_votes} | Text: {review_text}"
                )
            )

        user_prompt = (
            f"Retrieved reviews:\n{chr(10).join(context_lines)}\n\n"
            f"User question: {message}\n\n"
            "Please answer using only the retrieved review context above."
        )

        response = llm_service.chat(_SYSTEM_PROMPT, user_prompt)
        return {
            "response": response,
            "context_reviews": [
                {
                    "id": hit.id,
                    "review_id": hit.review_id,
                    "isbn": hit.isbn,
                    "rating": hit.rating,
                    "score": hit.score,
                }
                for hit in hits
            ],
        }


reviews_chat_service = ReviewsChatService()
