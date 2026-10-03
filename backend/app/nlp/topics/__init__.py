"""Topic modeling package using BERTopic, UMAP, HDBSCAN, and sentence embeddings."""

from app.nlp.topics.embedder import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL_NAME,
    SentenceEmbedder,
)
from app.nlp.topics.modeler import (
    DiscoveredTopic,
    TopicModeler,
    generate_topic_name,
)

__all__ = [
    "DiscoveredTopic",
    "EMBEDDING_DIMENSIONS",
    "EMBEDDING_MODEL_NAME",
    "SentenceEmbedder",
    "TopicModeler",
    "generate_topic_name",
]
