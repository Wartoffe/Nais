import logging

from repository.books_repository import books_repository
from repository.reviews_repository import reviews_repository
from services.minilm_embedding_service import minilm_service
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a knowledgeable librarian and book expert helping readers discover and understand books.

You answer questions based strictly on the provided book catalog and review data.

Rules:
- Base your answer only on the books and reviews given as context.
- If the context does not contain enough information, say: "I don't have enough information in the catalog to fully answer this."
- Be enthusiastic but concise — readers want recommendations, not essays.
- Keep your answer under 250 words.
- Do not invent titles, authors, or review content."""


_SYSTEM_PROMPT_REVIEWS = """You are a literary critic helping readers decide whether a book is worth reading.

You summarize and interpret reader reviews based strictly on the review excerpts provided.

Rules:
- Draw conclusions only from the review text given.
- If reviews are insufficient, say: "I don't have enough reviews to give a confident opinion."
- Highlight both praise and criticism where present.
- Keep your answer under 200 words.
- Do not fabricate reviewer opinions."""


class BooksChatService:
    """RAG chat service for the books + reviews domain.

    Two entry points:
      • chat()         – semantic book discovery (queries the books collection)
      • reviews_chat() – opinion summary    (queries the reviews collection)
    """

    # ── Book discovery ────────────────────────────────────────────────────────

    def chat(self, message: str) -> dict:
        """Find relevant books via ANN search, then ask the LLM to recommend."""
        qvec = minilm_service.encode_one(message)
        hits = books_repository.search_dense([qvec], top_k=5)[0]

        if not hits:
            return {
                "response": (
                    "I couldn't find any relevant books in the catalog for your query."
                ),
                "sources": [],
            }

        # Build a compact text block for each book hit
        book_snippets = []
        for h in hits:
            snippet = (
                f"Title: {h.get('title', 'N/A')} | "
                f"Author: {h.get('author', 'N/A')} | "
                f"Genre: {h.get('genre', 'N/A')} | "
                f"Year: {h.get('year', 'N/A')} | "
                f"Language: {h.get('language', 'N/A')}\n"
                f"Description: {h.get('description', '')}"
            )
            book_snippets.append(snippet)

        context = "\n\n".join(
            f"[Book {i + 1}]\n{s}" for i, s in enumerate(book_snippets)
        )

        user_prompt = (
            f"Catalog excerpts:\n{context}\n\n"
            f"Reader question: {message}\n\n"
            "Please recommend or discuss the books above in relation to the reader's question."
        )

        response = llm_service.chat(_SYSTEM_PROMPT, user_prompt)

        sources = [
            {
                "title":  h.get("title"),
                "author": h.get("author"),
                "isbn":   h.get("isbn"),
                "genre":  h.get("genre"),
                "year":   h.get("year"),
            }
            for h in hits
        ]

        return {"response": response, "sources": sources}

    # ── Review opinion summary ────────────────────────────────────────────────

    def reviews_chat(self, message: str) -> dict:
        """Find relevant reviews via ANN search, then ask the LLM to summarise sentiment."""
        qvec = minilm_service.encode_one(message)
        hits = reviews_repository.search_semantic([qvec], top_k=5)[0]

        if not hits:
            return {
                "response": (
                    "I couldn't find any relevant reviews in the database for your query."
                ),
                "sources": [],
            }

        review_snippets = []
        for h in hits:
            snippet = (
                f"ISBN: {h.get('isbn', 'N/A')} | "
                f"Rating: {h.get('rating', 'N/A')}/5 | "
                f"User type: {h.get('user_type', 'N/A')}\n"
                f"Review: {h.get('review_text', '')}"
            )
            review_snippets.append(snippet)

        context = "\n\n".join(
            f"[Review {i + 1}]\n{s}" for i, s in enumerate(review_snippets)
        )

        user_prompt = (
            f"Reader reviews:\n{context}\n\n"
            f"User question: {message}\n\n"
            "Please summarise what readers think, based on the reviews above."
        )

        response = llm_service.chat(_SYSTEM_PROMPT_REVIEWS, user_prompt)

        sources = [h.get("review_text", "") for h in hits]

        return {"response": response, "sources": sources}


books_chat_service = BooksChatService()
