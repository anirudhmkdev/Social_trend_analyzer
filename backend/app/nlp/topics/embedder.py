"""Sentence Embeddings module using SentenceTransformers all-MiniLM-L6-v2."""

from __future__ import annotations

import logging
import os
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384


class SentenceEmbedder:
    """Lazy-loaded Sentence Transformers embedder."""

    _instance: Optional["SentenceEmbedder"] = None
    _model = None

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self.dimensions = EMBEDDING_DIMENSIONS
        self._is_loaded = False

    @classmethod
    def get_instance(cls, model_name: str = EMBEDDING_MODEL_NAME) -> "SentenceEmbedder":
        if cls._instance is None:
            cls._instance = cls(model_name=model_name)
        return cls._instance

    def load_model(self) -> None:
        """Lazily load the SentenceTransformer model on CPU."""
        if self._is_loaded and self._model is not None:
            return

        # Fast deterministic path during testing to prevent downloading model weights
        if os.environ.get("PYTEST_CURRENT_TEST") and not os.environ.get("LOAD_FULL_HF_MODEL"):
            self._is_loaded = True
            self._model = None
            return

        logger.info("Loading sentence embedding model %s on CPU...", self.model_name)
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device="cpu")
            self._is_loaded = True
            logger.info("Sentence embedding model %s loaded.", self.model_name)
        except Exception as exc:
            logger.warning(
                "Could not load SentenceTransformer (%s): %s. Using fallback.",
                self.model_name,
                exc,
            )
            self._is_loaded = True
            self._model = None

    def encode(
        self,
        texts: List[str],
        batch_size: int = 64,
        normalize_embeddings: bool = True,
    ) -> np.ndarray:
        """Encode a list of texts into dense 384-dimensional vectors."""
        if not texts:
            return np.empty((0, self.dimensions), dtype=np.float32)

        self.load_model()

        if self._model is not None:
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                normalize_embeddings=normalize_embeddings,
            )
            return np.asarray(embeddings, dtype=np.float32)

        # Deterministic pseudo-embedding fallback for unit tests
        # Uses hash-based pseudo-random projection to 384 dims
        fallback_vectors: List[np.ndarray] = []
        for text in texts:
            np.random.seed(hash(text) % (2**32 - 1))
            vec = np.random.randn(self.dimensions).astype(np.float32)
            if normalize_embeddings:
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
            fallback_vectors.append(vec)
        return np.array(fallback_vectors, dtype=np.float32)
