import logging

from repository.sciq_repository import sciq_repository
from services.minilm_embedding_service import minilm_service
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a science tutor helping students understand natural science topics (physics, chemistry, biology, earth science).

You answer questions based strictly on the provided reference passages.

Rules:
- Base your answer only on the passages given.
- If the passages do not contain enough information, say: "I don't have enough information in the provided passages to fully answer this."
- Explain concepts clearly and simply, as if talking to a high school student.
- Keep your answer under 200 words.
- Do not make up facts."""


class SciQChatService:

    def chat(self, message: str) -> dict:
        qvec = minilm_service.encode_one(message)
        hits  = sciq_repository.search([qvec], top_k=4)[0]

        if not hits:
            return {
                "response": "I couldn't find any relevant passages in the scientific corpus for your question.",
                "sources":  [],
            }

        passages = [h.get("support_text", "") for h in hits]

        context = "\n\n".join(
            f"[Passage {i + 1}] {p}" for i, p in enumerate(passages)
        )

        user_prompt = (
            f"Reference passages:\n{context}\n\n"
            f"Student question: {message}\n\n"
            "Please answer the question based on the passages above."
        )

        response = llm_service.chat(_SYSTEM_PROMPT, user_prompt)

        return {
            "response": response,
            "sources":  passages,
        }


sciq_chat_service = SciQChatService()
