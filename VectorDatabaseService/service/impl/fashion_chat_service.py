import logging

from repository.fashion_lab_repository import fashion_lab_repository
from services.embedding_service import embedding_service
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

# The Persona/Instruction set that guides the LLM's behavior and tone
_SYSTEM_PROMPT = """You are a personal fashion stylist assistant for an online clothing store.
The user will describe what they have or what they want to wear, and you will recommend a complete outfit using items from the store catalog.

Rules:
- Always reference exact item names from the catalog.
- Keep your recommendation concise (under 150 words).
- Mention why the items work well together (color, style, occasion).
- If the catalog items are not enough to complete an outfit, say so honestly."""


class FashionChatService:
    """Service that combines vector search and an LLM for a Retrieval-Augmented Generation (RAG) chatbot."""

    def chat(self, message: str) -> dict:
        """Processes a user message to find relevant clothes and generate a stylist recommendation."""
        
        # Step 1: Convert user text into a vector for searching the database
        qvec = embedding_service.encode_text_one(message)

        # Step 2: Retrieve the top 10 most similar clothing items from the repository
        hits  = fashion_lab_repository.search([qvec], "text_embedding", top_k=10)[0]

        # Early exit if no items are found in the database
        if not hits:
            return {
                "response":      "I couldn't find any relevant items in the catalog for your request.",
                "context_items": [],
            }

        # Step 3: Format the metadata of the found items into a text block for the LLM
        context_lines = []
        for h in hits:
            name     = h.get("product_name", "Unknown")
            category = h.get("article_type",    "")
            colour   = h.get("base_colour",      "")
            gender   = h.get("gender",           "")
            season   = h.get("season",           "")
            context_lines.append(f"- {name} | {category} | {colour} | {gender} | {season}")

        context = "\n".join(context_lines)

        # Step 4: Construct the final prompt combining the data (context) and the user's question
        user_prompt = (
            f"Available items from our catalog:\n{context}\n\n"
            f"Customer request: {message}\n\n"
            "Please recommend a complete outfit using items from the catalog above."
        )

        # Step 5: Call the local LLM service to generate the final human-like response
        response = llm_service.chat(_SYSTEM_PROMPT, user_prompt)

        return {
            "response":      response,
            "context_items": [h.get("product_name", "") for h in hits],
        }


fashion_chat_service = FashionChatService()
