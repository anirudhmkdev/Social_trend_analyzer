"""Sentiment analysis module using CardiffNLP Twitter-RoBERTa.

Model: cardiffnlp/twitter-roberta-base-sentiment-latest
License: CC-BY-4.0 (~124M tweets training, 3 labels: negative, neutral, positive)
CPU-only, lazy-loaded, in-memory cached, batched inference.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SENTIMENT_MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
SENTIMENT_MODEL_LICENSE = "CC-BY-4.0"
SENTIMENT_LABELS = ["negative", "neutral", "positive"]


@dataclass
class SentimentResultData:
    label: str
    confidence: float
    score_positive: float
    score_neutral: float
    score_negative: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SentimentAnalyzer:
    """Lazy-loaded Twitter-RoBERTa sentiment classifier."""

    _instance: Optional["SentimentAnalyzer"] = None
    _pipeline: Any = None

    def __init__(self, model_name: str = SENTIMENT_MODEL_NAME):
        self.model_name = model_name
        self.license = SENTIMENT_MODEL_LICENSE
        self.labels = SENTIMENT_LABELS
        self._is_loaded = False

    @classmethod
    def get_instance(cls, model_name: str = SENTIMENT_MODEL_NAME) -> "SentimentAnalyzer":
        if cls._instance is None:
            cls._instance = cls(model_name=model_name)
        return cls._instance

    def load_model(self) -> None:
        """Lazily load the HuggingFace pipeline on CPU and cache in memory."""
        if self._is_loaded and self._pipeline is not None:
            return

        logger.info("Loading sentiment model: %s on CPU...", self.model_name)
        try:
            from transformers import pipeline

            # Load sentiment pipeline for CPU
            self._pipeline = pipeline(
                "text-classification",
                model=self.model_name,
                tokenizer=self.model_name,
                device=-1,  # CPU
                top_k=None,  # Return all 3 class scores
                truncation=True,
                max_length=128,
            )
            self._is_loaded = True
            logger.info("Sentiment model %s loaded successfully.", self.model_name)
        except Exception as exc:
            raise RuntimeError(
                f"Sentiment model {self.model_name} is unavailable. "
                "Download the model weights and retry analysis."
            ) from exc

    def predict(self, text: str) -> SentimentResultData:
        """Predict sentiment for a single text string."""
        return self.predict_batch([text])[0]

    def metadata(self) -> Dict[str, Any]:
        config = getattr(getattr(self._pipeline, "model", None), "config", None)
        return {
            "model": self.model_name,
            "revision": getattr(config, "_commit_hash", None),
            "max_tokens": 128,
            "device": "cpu",
        }

    def predict_batch(self, texts: List[str], batch_size: int = 32) -> List[SentimentResultData]:
        """Perform batched sentiment inference."""
        if not texts:
            return []

        self.load_model()

        results: List[SentimentResultData] = []
        # Batch inference
        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            cleaned_chunk = [t if t.strip() else "neutral" for t in chunk]
            outputs: Any = self._pipeline(cleaned_chunk, batch_size=len(chunk))

            for out in outputs:
                # out can be a list of dicts or single dict
                scores = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
                items = out if isinstance(out, list) else [out]
                for item in items:
                    raw_label = str(item.get("label", "")).lower()
                    score = float(item.get("score", 0.0))
                    if "pos" in raw_label or raw_label == "label_2":
                        scores["positive"] = score
                    elif "neg" in raw_label or raw_label == "label_0":
                        scores["negative"] = score
                    elif "neu" in raw_label or raw_label == "label_1":
                        scores["neutral"] = score
                    else:
                        scores[raw_label] = score

                best_label = max(scores, key=lambda k: scores[k])
                best_conf = scores[best_label]

                results.append(
                    SentimentResultData(
                        label=best_label,
                        confidence=round(best_conf, 4),
                        score_positive=round(scores["positive"], 4),
                        score_neutral=round(scores["neutral"], 4),
                        score_negative=round(scores["negative"], 4),
                    )
                )

        return results
