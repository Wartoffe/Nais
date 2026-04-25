import logging

import numpy as np
from sentence_transformers import SentenceTransformer

from config import BOOKS_EMBEDDING_MODEL, BOOKS_EMBEDDING_DIM

logger = logging.getLogger(__name__)


class MiniLMEmbeddingService:
    """Service for generating text embeddings using the MiniLM model.

    Domain-agnostic: used by Books and Reviews domains.
    All three share the same model (all-MiniLM-L6-v2) and dimension (384),
    so a single singleton instance serves the entire application.
    """

    def __init__(
        self,
        model_name: str = BOOKS_EMBEDDING_MODEL,
        dim: int = BOOKS_EMBEDDING_DIM,
    ):
        logger.info("Loading MiniLM model '%s' ...", model_name)
        self._model = SentenceTransformer(model_name)
        self._dim = dim
        logger.info("MiniLM model loaded (dim=%d).", self._dim)

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Converts a batch of texts into normalized vector representations."""
        return self._model.encode(
            texts,
            batch_size=64,           
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,  
        ).tolist()

    def encode_one(self, text: str) -> list[float]:
        """Encodes a single string into its vector form."""
        return self.encode([text])[0]

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        """Calculates the dot-product similarity between two pre-normalized vectors."""
        va = np.array(a, dtype=np.float32)
        vb = np.array(b, dtype=np.float32)
        return float(np.dot(va, vb))

    def zero_vector(self) -> list[float]:
        """Returns a zero vector matching this model's output dimension."""
        return [0.0] * self._dim


minilm_service = MiniLMEmbeddingService()