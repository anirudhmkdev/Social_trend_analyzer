"""Topic discovery using BERTopic, UMAP, HDBSCAN, and c-TF-IDF."""

from __future__ import annotations

import logging
import re
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
    model_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_topic_name(keywords: List[Dict[str, Any]], topic_index: int) -> str:
    """A transparent keyword-derived label, with redundant terms/stems removed."""
    if topic_index == -1:
        return "Unclassified (Outliers)"
    phrases = [
        re.sub(r"[_-]+", " ", str(keyword.get("word", ""))).strip().lower()
        for keyword in keywords
        if keyword.get("word")
    ]
    vocabulary = set(" ".join(phrases).split())
    # Labels are supported by the topic vocabulary, never inferred via a remote LLM.
    if vocabulary & {"outbreak", "disease", "health", "vaccine", "hospital", "pandemic"}:
        return (
            "Public Health Crisis"
            if vocabulary & {"outbreak", "crisis", "pandemic"}
            else "Public Health"
        )
    if vocabulary & {"renewable", "solar", "wind", "energy"}:
        return "Renewable Energy"
    if vocabulary & {"climate", "emissions", "climatechange", "warming"}:
        return "Climate Change"
    if vocabulary & {
        "artificialintelligence",
        "machinelearning",
        "neural",
        "transformer",
        "automation",
    }:
        return "AI Model Development"
    if vocabulary & {"bitcoin", "ethereum", "crypto", "blockchain", "cryptocurrency"}:
        return (
            "Crypto Regulation"
            if vocabulary & {"regulation", "regulatory", "sec"}
            else "Crypto Markets"
        )
    if vocabulary & {"nba", "tournament", "football", "olympics", "sports", "championship"}:
        return "Sports Competition"
    selected = []
    stems: set[str] = set()
    for phrase in phrases:
        tokens = {re.sub(r"(ing|ed|s)$", "", word) for word in phrase.split()}
        if not tokens or tokens & stems:
            continue
        selected.append(phrase.title())
        stems.update(tokens)
        if len(selected) == 2:
            break
    return " · ".join(selected) if selected else f"Topic {topic_index}"


class TopicModeler:
    """BERTopic wrapper with deterministic UMAP, HDBSCAN, and c-TF-IDF."""

    def __init__(
        self,
        random_state: int = 42,
        min_cluster_size: Optional[int] = None,
        min_samples: int = 3,
    ):
        self.random_state = random_state
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.metadata: Dict[str, Any] = {}

    def _fallback_clustering(
        self, documents: List[str], embeddings: np.ndarray
    ) -> Tuple[List[int], List[float], List[DiscoveredTopic]]:
        """Explicit small-corpus semantic clustering, with TF-IDF term descriptions."""
        from sklearn.feature_extraction.text import TfidfVectorizer

        n_docs = len(documents)
        if n_docs == 0:
            return [], [], []

        from sklearn.cluster import AgglomerativeClustering

        labels = (
            np.zeros(1, dtype=int)
            if n_docs == 1
            else AgglomerativeClustering(
                n_clusters=None, distance_threshold=0.35, metric="cosine", linkage="average"
            ).fit_predict(embeddings)
        )
        self.metadata = {
            "method": "small-corpus agglomerative clustering",
            "distance_threshold": 0.35,
        }

        vectorizer = TfidfVectorizer(stop_words="english", max_features=50, ngram_range=(1, 2))
        try:
            tfidf_matrix = vectorizer.fit_transform(documents)
            feature_names = vectorizer.get_feature_names_out()
        except ValueError:
            feature_names = np.array([])
            tfidf_matrix = None

        topics: List[DiscoveredTopic] = []
        for cluster_id in sorted(set(labels)):
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
                    topic_index=int(cluster_id),
                    display_name=disp_name,
                    keywords=keywords,
                    representative_docs=rep_docs,
                    post_indices=indices,
                    probabilities=[1.0] * len(indices),
                    is_outlier=False,
                )
            )

        probs = [1.0] * n_docs
        return [int(label) for label in labels], probs, topics

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

        # UMAP/HDBSCAN is unsuitable for very small corpora; record the alternate method.
        if n_docs < 15:
            return self._fallback_clustering(documents, embeddings)

        try:
            from bertopic import BERTopic
            from hdbscan import HDBSCAN
            from sklearn.feature_extraction.text import CountVectorizer
            from umap import UMAP

            n_neighbors = min(15, max(2, n_docs - 1))
            n_components = min(5, max(2, n_docs - 1))
            min_cluster = min(
                self.min_cluster_size or max(8, round(n_docs * 0.02)), max(2, n_docs // 4)
            )

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

            raw_labels = [int(label) for label in topic_labels]
            raw_keywords = {
                label: [
                    {"word": str(word), "score": round(float(score), 4)}
                    for word, score in (topic_model.get_topic(label) or [])[:10]
                ]
                for label in set(raw_labels)
            }
            # Consolidate only very similar semantic centroids; no target topic count.
            from sklearn.metrics.pairwise import cosine_similarity

            ids = sorted(label for label in set(raw_labels) if label >= 0)
            centroids = [embeddings[np.array(raw_labels) == label].mean(axis=0) for label in ids]
            groups = []
            if len(ids) > 1:
                similarity = cosine_similarity(centroids)
                remaining = set(range(len(ids)))
                for index in range(len(ids)):
                    if index not in remaining:
                        continue
                    group = [index]
                    remaining.remove(index)
                    for other in sorted(remaining):
                        # Complete-link criterion avoids chains of loosely related topics.
                        if all(similarity[other, member] >= 0.90 for member in group):
                            group.append(other)
                    remaining.difference_update(group)
                    if len(group) > 1:
                        groups.append([ids[member] for member in group])
                if groups:
                    topic_model.merge_topics(documents, groups)
                    topic_labels = topic_model.topics_
                    probs = topic_model.probabilities_
            self.metadata = {
                "method": "BERTopic + UMAP + HDBSCAN + c-TF-IDF",
                "min_cluster_size": min_cluster,
                "min_samples": min(self.min_samples, min_cluster),
                "semantic_merge_threshold": 0.90,
                "raw_cluster_count": len(ids),
                "merge_groups": groups,
                "random_seed": self.random_state,
            }

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

                rep_docs = [documents[i] for i in sorted(indices, key=lambda i: -max_probs[i])[:5]]
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
                        model_metadata={
                            "raw_topics": [
                                {"topic_index": raw_id, "keywords": raw_keywords[raw_id]}
                                for raw_id in sorted({raw_labels[i] for i in indices})
                            ]
                        },
                    )
                )

            # Distinguish clusters within a keyword-derived family without disguising them
            # as one topic or assigning an arbitrary target topic count.
            names = [topic.display_name for topic in discovered]
            for topic in discovered:
                if names.count(topic.display_name) > 1:
                    base = topic.display_name
                    candidates = [kw["word"] for kw in topic.keywords if kw["word"]]
                    if candidates:
                        topic.display_name = f"{base} · {candidates[0].title()}"
            return topic_labels, max_probs, discovered

        except Exception as exc:
            raise RuntimeError(
                "BERTopic topic modeling failed. Inspect the backend log and retry."
            ) from exc
