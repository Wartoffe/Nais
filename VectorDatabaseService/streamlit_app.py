import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://vector-database-service:8000")

st.set_page_config(
    page_title="AI Assistant — Vector DB Demo",
    page_icon="🤖",
    layout="centered",
)

st.title("AI Assistant")
st.caption(f"Powered by Ollama · Vector DB: Milvus · API: {API_URL}")

# ── Ollama status badge ───────────────────────────────────────────────────────
try:
    health = requests.get(f"{API_URL}/api/v1/chat/health", timeout=3).json()
    if health.get("ollama_available"):
        st.success(f"LLM online — model: `{health.get('model')}`", icon="✅")
    else:
        st.warning("LLM not ready yet — Ollama may still be loading the model.", icon="⏳")
except Exception:
    st.error("Cannot reach the API. Make sure docker compose is running.", icon="🔴")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_books, tab_reviews = st.tabs([
    "📚 Book Finder",
    "⭐ Review Insights",
])


# ── Books tab ─────────────────────────────────────────────────────────────────
with tab_books:
    st.subheader("Book Finder")
    st.caption(
        "Describe what you're in the mood to read. I search the books catalog in Milvus "
        "and ask an LLM to recommend from what's available."
    )

    if "books_history" not in st.session_state:
        st.session_state.books_history = []

    for msg in st.session_state.books_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("Books retrieved from catalog", expanded=False):
                    for book in msg["sources"]:
                        st.markdown(
                            f"- **{book.get('title')}** by {book.get('author')} "
                            f"({book.get('genre')}, {book.get('year')}) — ISBN: `{book.get('isbn')}`"
                        )

    if prompt := st.chat_input(
        "e.g. Looking for a sci-fi novel about space exploration",
        key="books_input",
    ):
        st.session_state.books_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching catalog and generating recommendation…"):
                try:
                    resp = requests.post(
                        f"{API_URL}/api/v1/books/chat",
                        json={"message": prompt},
                        timeout=120,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    response_text = data["response"]
                    sources = data.get("sources", [])

                    st.markdown(response_text)
                    if sources:
                        with st.expander("Books retrieved from catalog", expanded=False):
                            for book in sources:
                                st.markdown(
                                    f"- **{book.get('title')}** by {book.get('author')} "
                                    f"({book.get('genre')}, {book.get('year')}) — ISBN: `{book.get('isbn')}`"
                                )
                except requests.exceptions.Timeout:
                    response_text = "⏳ Request timed out. The LLM may still be warming up — try again in a moment."
                    sources = []
                    st.warning(response_text)
                except Exception as exc:
                    response_text = f"❌ Error: {exc}"
                    sources = []
                    st.error(response_text)

        st.session_state.books_history.append({
            "role":    "assistant",
            "content": response_text,
            "sources": sources,
        })

    if st.session_state.books_history:
        if st.button("Clear conversation", key="clear_books"):
            st.session_state.books_history = []
            st.rerun()


# ── Reviews tab ───────────────────────────────────────────────────────────────
with tab_reviews:
    st.subheader("Review Insights")
    st.caption(
        "Ask what readers think about a book, author, or genre. I search the reviews "
        "collection in Milvus and ask an LLM to summarise the sentiment."
    )

    if "reviews_history" not in st.session_state:
        st.session_state.reviews_history = []

    for msg in st.session_state.reviews_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("Retrieved reviews", expanded=False):
                    for i, src in enumerate(msg["sources"], 1):
                        st.markdown(f"**Review {i}:** {src}")

    if prompt := st.chat_input(
        "e.g. What do readers think about dystopian fiction?",
        key="reviews_input",
    ):
        st.session_state.reviews_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching reviews and summarising sentiment…"):
                try:
                    resp = requests.post(
                        f"{API_URL}/api/v1/books/reviews/chat",
                        json={"message": prompt},
                        timeout=120,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    response_text = data["response"]
                    sources = data.get("sources", [])

                    st.markdown(response_text)
                    if sources:
                        with st.expander("Retrieved reviews", expanded=False):
                            for i, src in enumerate(sources, 1):
                                st.markdown(f"**Review {i}:** {src}")
                except requests.exceptions.Timeout:
                    response_text = "⏳ Request timed out. The LLM may still be warming up — try again in a moment."
                    sources = []
                    st.warning(response_text)
                except Exception as exc:
                    response_text = f"❌ Error: {exc}"
                    sources = []
                    st.error(response_text)

        st.session_state.reviews_history.append({
            "role":    "assistant",
            "content": response_text,
            "sources": sources,
        })

    if st.session_state.reviews_history:
        if st.button("Clear conversation", key="clear_reviews"):
            st.session_state.reviews_history = []
            st.rerun()