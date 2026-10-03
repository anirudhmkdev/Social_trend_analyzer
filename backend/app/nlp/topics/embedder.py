"""Sentence Embeddings module using SentenceTransformers all-MiniLM-L6-v2."""

from __future__ import annotations

import logging
from typing import Any, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384


class SentenceEmbedder:
    """Lazy-loaded Sentence Transformers embedder."""

    _instance: Optional["SentenceEmbedder"] = None
    _model: Any = None

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

        logger.info("Loading sentence embedding model %s on CPU...", self.model_name)
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device="cpu")
            self._is_loaded = True
            logger.info("Sentence embedding model %s loaded.", self.model_name)
        except Exception as exc:
            raise RuntimeError(
                f"Embedding model {self.model_name} is unavailable. "
                "Download the model weights and retry analysis."
            ) from exc

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

        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=normalize_embeddings,
        )
        return np.asarray(embeddings, dtype=np.float32)

    def metadata(self) -> dict:
        first = self._model._first_module() if hasattr(self._model, "_first_module") else None
        config = getattr(getattr(first, "auto_model", None), "config", None)
        return {
            "model": self.model_name,
            "revision": getattr(config, "_commit_hash", None),
            "dimensions": self.dimensions,
            "device": "cpu",
        }
