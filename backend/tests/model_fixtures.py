"""Explicit inference fixtures for contract tests; never imported by production code.

These verify pipeline persistence/UI behavior, not model accuracy. Real weights are
exercised separately by scripts/full_nlp_smoke.py.
"""

import hashlib
import re

import numpy as np


class FixtureEmbeddings:
    def encode(self, texts, **kwargs):
        vectors = np.zeros((len(texts), 384), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in re.findall(r"[a-z]+", text.lower()):
                index = int(hashlib.sha256(token.encode()).hexdigest()[:8], 16) % 384
                vectors[row, index] += 1
            norm = np.linalg.norm(vectors[row])
            vectors[row] /= norm or 1
        return vectors


def fixture_sentiment(texts, **kwargs):
    return [
        [
            {"label": "positive", "score": 0.2},
            {"label": "neutral", "score": 0.7},
            {"label": "negative", "score": 0.1},
        ]
        for _ in texts
    ]


def install_model_fixtures():
    import spacy

    from app.nlp.enrichment.ner import EntityRecognizer
    from app.nlp.sentiment.classifier import SentimentAnalyzer
    from app.nlp.topics.embedder import SentenceEmbedder

    sentiment = SentimentAnalyzer()
    sentiment._pipeline = fixture_sentiment
    sentiment._is_loaded = True
    SentimentAnalyzer._instance = sentiment
    embedder = SentenceEmbedder()
    embedder._model = FixtureEmbeddings()
    embedder._is_loaded = True
    SentenceEmbedder._instance = embedder
    ner = EntityRecognizer()
    ner._nlp = spacy.blank("en")
    ruler = ner._nlp.add_pipe("entity_ruler")
    ruler.add_patterns(
        [
            {"label": "ORG", "pattern": name}
            for name in ["OpenAI", "Google", "DeepMind", "Microsoft", "Meta"]
        ]
        + [{"label": "PERSON", "pattern": "Sam Altman"}, {"label": "GPE", "pattern": "Paris"}]
    )
    ner._is_loaded = True
    ner.status = "available"
    EntityRecognizer._instance = ner
