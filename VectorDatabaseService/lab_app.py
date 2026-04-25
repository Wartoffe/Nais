import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controller.reviews_controller import router as reviews_router
from controller.books_controller import router as books_router
from controller.books_chat_controller import router as books_chat_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s")

app = FastAPI(
    title="Vector Database Service — Library",
    description="Books and reviews vector search API with semantic, hybrid, and chat endpoints.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(books_router)
app.include_router(reviews_router)
app.include_router(books_chat_router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "collection": "books + reviews"}


if __name__ == "__main__":
    uvicorn.run("lab_app:app", host="0.0.0.0", port=8000, reload=False)
