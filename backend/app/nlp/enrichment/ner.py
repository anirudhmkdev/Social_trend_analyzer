"""Conservative spaCy NER; absent weights explicitly disable this optional stage."""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Set

from app.nlp.preprocessing.cleaner import TextPreprocessor

logger = logging.getLogger(__name__)
NER_MODEL_NAME = "en_core_web_sm"
ALLOWED_ENTITY_LABELS: Set[str] = {"PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "NORP"}
GENERIC_ENTITIES = {
    "new",
    "record",
    "investors",
    "scientists",
    "fans",
    "countries",
    "experts",
    "highlights",
    "how",
    "breakthrough",
    "researchers",
    "debate",
    "renewable",
    "today",
    "tomorrow",
    "yesterday",
    "ai",
    "crypto",
    "climate",
    "health",
    "sports",
}


@dataclass
class ExtractedEntity:
    text: str
    normalized_text: str
    label: str
    start_char: int
    end_char: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EntityRecognizer:
    _instance: Optional["EntityRecognizer"] = None
    _nlp: Any = None

    def __init__(self, model_name: str = NER_MODEL_NAME):
        self.model_name = model_name
        self.allowed_labels = ALLOWED_ENTITY_LABELS
        self._is_loaded = False
        self.status = "not_loaded"
        self.error: Optional[str] = None

    @classmethod
    def get_instance(cls, model_name: str = NER_MODEL_NAME) -> "EntityRecognizer":
        if cls._instance is None:
            cls._instance = cls(model_name)
        return cls._instance

    def load_model(self) -> None:
        if self._is_loaded:
            return
        try:
            import spacy

            self._nlp = spacy.load(
                self.model_name, disable=["tagger", "parser", "attribute_ruler", "lemmatizer"]
            )
            self.status = "available"
        except Exception:
            self._nlp = None
            self.status = "unavailable"
            self.error = (
                f"NER omitted: install the spaCy model {self.model_name}, then run analysis again."
            )
            logger.warning(self.error)
        self._is_loaded = True

    def metadata(self) -> Dict[str, Any]:
        return {
            "model": self.model_name,
            "status": self.status,
            "warning": self.error,
            "version": self._nlp.meta.get("version") if self._nlp is not None else None,
        }

    def extract_from_texts(
        self, raw_texts: List[str], batch_size: int = 64
    ) -> List[List[ExtractedEntity]]:
        if not raw_texts:
            return []
        self.load_model()
        if self._nlp is None:
            return [[] for _ in raw_texts]
        # Hashtag tokens are topical annotations, not evidence of named entities.
        ner_texts = [
            TextPreprocessor.derive_ner_text(re.sub(r"#\w+", " ", text)) for text in raw_texts
        ]
        results: List[List[ExtractedEntity]] = []
        for doc in self._nlp.pipe(ner_texts, batch_size=batch_size):
            entities = []
            seen = set()
            for ent in doc.ents:
                clean = re.sub(r"\s+", " ", ent.text).strip(" \t\n.,;:!?")
                normalized = clean.casefold()
                key = (normalized, ent.label_, ent.start_char)
                if (
                    ent.label_ in self.allowed_labels
                    and len(clean) >= 2
                    and normalized not in GENERIC_ENTITIES
                    and not (ent.label_ == "PERSON" and clean.islower())
                    and any(char.isalpha() for char in clean)
                    and key not in seen
                ):
                    seen.add(key)
                    entities.append(
                        ExtractedEntity(clean, normalized, ent.label_, ent.start_char, ent.end_char)
                    )
            results.append(entities)
        return results
