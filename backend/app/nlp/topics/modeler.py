"""Topic discovery using BERTopic, UMAP, HDBSCAN, and c-TF-IDF."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredTopic:
    topic_index: int
    display_name: str
    keywords: List[Dict[str, Any]]  # [{"word": str, "score": float}]
    representative_docs: List[str]
    post_indices: List[int]
    probabilities: List[float] = field(default_factory=list)
    is_outlier: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_topic_name(keywords: List[Dict[str, Any]], topic_index: int) -> str:
    """Generate human-readable topic name from top 3 keywords.

    Example: [{'word': 'climate'}, {'word': 'emissions'}, {'word': 'renewable'}]
             -> 'Climate, Emissions & Renewable'
    """
    if topic_index == -1:
        return "Unclassified (Outliers)"

    if not keywords:
        return f"Topic {topic_index}"

    top_words: List[str] = [str(k["word"]).capitalize() for k in keywords[:3] if k.get("word")]
    if not top_words:
        return f"Topic {topic_index}"

    if len(top_words) == 1:
        return top_words[0]
    elif len(top_words) == 2:
        return f"{top_words[0]} & {top_words[1]}"
    else:
        return f"{top_words[0]}, {top_words[1]} & {top_words[2]}"


class TopicModeler:
    """BERTopic wrapper with deterministic UMAP, HDBSCAN, and c-TF-IDF."""

    def __init__(
        self,
        random_state: int = 42,
        min_cluster_size: int = 5,
        min_samples: int = 3,
    ):
        self.random_state = random_state
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples

    def _fallback_clustering(
        self, documents: List[str], embeddings: np.ndarray
    ) -> Tuple[List[int], List[float], List[DiscoveredTopic]]:
        """Deterministic lexical/TF-IDF fallback clustering for small sample sizes or tests."""
        from sklearn.feature_extraction.text import TfidfVectorizer

        n_docs = len(documents)
        if n_docs == 0:
            return [], [], []

        # If very few docs, group into 1 or 2 small topics
        k = min(3, max(1, n_docs // 3))
        from sklearn.cluster import KMeans

        kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=5)
        labels = kmeans.fit_predict(embeddings)

        vectorizer = TfidfVectorizer(stop_words="english", max_features=50, ngram_range=(1, 2))
        try:
            tfidf_matrix = vectorizer.fit_transform(documents)
            feature_names = vectorizer.get_feature_names_out()
        except ValueError:
            feature_names = np.array([])
            tfidf_matrix = None

        topics: List[DiscoveredTopic] = []
        for cluster_id in range(k):
            indices = [i for i, label in enumerate(labels) if label == cluster_id]
            if not indices:
                continue

            keywords = []
            if tfidf_matrix is not None and len(feature_names) > 0:
                cluster_tfidf = tfidf_matrix[indices].mean(axis=0).A1  # type: ignore[attr-defined]
                top_kw_idx = cluster_tfidf.argsort()[::-1][:10]
                for idx in top_kw_idx:
                    if cluster_tfidf[idx] > 0:
                        keywords.append(
                            {
                                "word": str(feature_names[idx]),
                                "score": round(float(cluster_tfidf[idx]), 4),
                            }
                        )

            rep_docs = [documents[i] for i in indices[:5]]
            disp_name = generate_topic_name(keywords, cluster_id)

            topics.append(
                DiscoveredTopic(
                    topic_index=cluster_id,
                    display_name=disp_name,
                    keywords=keywords,
                    representative_docs=rep_docs,
                    post_indices=indices,
                    probabilities=[1.0] * len(indices),
                    is_outlier=False,
                )
            )

        probs = [1.0] * n_docs
        return list(labels), probs, topics

    def fit_transform(
        self,
        documents: List[str],
        embeddings: Optional[np.ndarray] = None,
    ) -> Tuple[List[int], List[float], List[DiscoveredTopic]]:
        """Fit topic model on documents and return (topic_labels, probabilities, topics)."""
        n_docs = len(documents)
        if n_docs == 0:
            return [], [], []

        if embeddings is None:
            from app.nlp.topics.embedder import SentenceEmbedder

            embeddings = SentenceEmbedder.get_instance().encode(documents)

        # For small sample sizes (< 15) or when BERTopic cannot run HDBSCAN reliably
        if n_docs < 15:
            return self._fallback_clustering(documents, embeddings)

        try:
            from bertopic import BERTopic
            from hdbscan import HDBSCAN
            from sklearn.feature_extraction.text import CountVectorizer
            from umap import UMAP

            n_neighbors = min(15, max(2, n_docs - 1))
            n_components = min(5, max(2, n_docs - 1))
            min_cluster = min(self.min_cluster_size, max(2, n_docs // 4))

            umap_model = UMAP(
                n_neighbors=n_neighbors,
                n_components=n_components,
                min_dist=0.0,
                metric="cosine",
                random_state=self.random_state,
            )
            hdbscan_model = HDBSCAN(
                min_cluster_size=min_cluster,
                min_samples=min(self.min_samples, min_cluster),
                metric="euclidean",
                prediction_data=True,
            )
            vectorizer_model = CountVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                min_df=1,
            )

            topic_model = BERTopic(
                umap_model=umap_model,
                hdbscan_model=hdbscan_model,
                vectorizer_model=vectorizer_model,
                nr_topics=None,  # Preserve natural clusters
                calculate_probabilities=True,
            )

            topic_labels, probs = topic_model.fit_transform(documents, embeddings=embeddings)

            # Convert numpy types to native Python
            topic_labels = [int(lbl) for lbl in topic_labels]
            if probs is not None:
                if isinstance(probs, np.ndarray) and probs.ndim > 1:
                    max_probs = [float(p.max()) for p in probs]
                else:
                    max_probs = [float(p) for p in probs]
            else:
                max_probs = [1.0] * n_docs

            # Build DiscoveredTopic objects
            unique_topics = sorted(list(set(topic_labels)))
            discovered: List[DiscoveredTopic] = []

            for topic_id in unique_topics:
                is_outlier = topic_id == -1
                indices = [i for i, t in enumerate(topic_labels) if t == topic_id]
                topic_probs = [max_probs[i] for i in indices]

                # Extract c-TF-IDF keywords from BERTopic
                keywords: List[Dict[str, Any]] = []
                try:
                    topic_words = topic_model.get_topic(topic_id)
                    if topic_words:
                        keywords = [
                            {"word": str(w), "score": round(float(s), 4)}
                            for w, s in topic_words[:10]
                        ]
                except Exception:
                    pass

                rep_docs = [documents[i] for i in indices[:5]]
                disp_name = generate_topic_name(keywords, topic_id)

                discovered.append(
                    DiscoveredTopic(
                        topic_index=topic_id,
                        display_name=disp_name,
                        keywords=keywords,
                        representative_docs=rep_docs,
                        post_indices=indices,
                        probabilities=topic_probs,
                        is_outlier=is_outlier,
                    )
                )

            return topic_labels, max_probs, discovered

        except Exception as exc:
            logger.warning(
                "BERTopic modeling failed (%s). Falling back to lexical clustering.", exc
            )
            return self._fallback_clustering(documents, embeddings)
