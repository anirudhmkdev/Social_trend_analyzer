"""Keyword extraction, TF-IDF analysis, and hashtag dynamics."""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


@dataclass
class KeywordItem:
    keyword: str
    keyword_type: str  # 'keyword', 'hashtag', 'ngram'
    frequency: int
    tfidf_score: Optional[float] = None
    growth_rate: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class KeywordExtractor:
    """Extract corpus-level TF-IDF keywords, n-grams, and hashtag metrics."""

    def __init__(self, max_features: int = 100):
        self.max_features = max_features

    def extract_keywords(
        self,
        cleaned_texts: List[str],
        top_n: int = 50,
    ) -> List[KeywordItem]:
        """Extract top TF-IDF keywords and n-grams from cleaned texts."""
        if not cleaned_texts or all(not t.strip() for t in cleaned_texts):
            return []

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=self.max_features,
            min_df=1,
            token_pattern=r"(?u)\b[a-zA-Z]{3,}\b",
        )

        try:
            tfidf_matrix = vectorizer.fit_transform(cleaned_texts)
            feature_names = vectorizer.get_feature_names_out()
            mean_tfidf = tfidf_matrix.mean(axis=0).A1  # type: ignore[attr-defined]

            # Count raw occurrences of features
            vocab = vectorizer.vocabulary_
            term_freqs: Counter[str] = Counter()
            for text in cleaned_texts:
                words = text.split()
                # Unigrams and bigrams
                for w in words:
                    if w in vocab:
                        term_freqs[w] += 1
                for i in range(len(words) - 1):
                    bg = f"{words[i]} {words[i + 1]}"
                    if bg in vocab:
                        term_freqs[bg] += 1

            sorted_indices = mean_tfidf.argsort()[::-1][:top_n]
            results: List[KeywordItem] = []
            for idx in sorted_indices:
                word = str(feature_names[idx])
                score = round(float(mean_tfidf[idx]), 4)
                freq = term_freqs.get(word, 1)
                kw_type = "ngram" if " " in word else "keyword"
                results.append(
                    KeywordItem(
                        keyword=word,
                        keyword_type=kw_type,
                        frequency=freq,
                        tfidf_score=score,
                    )
                )
            return results

        except ValueError as exc:
            logger.warning("TF-IDF extraction failed (%s). Returning frequency fallback.", exc)
            counter = Counter([w for t in cleaned_texts for w in t.split() if len(w) > 3])
            return [
                KeywordItem(
                    keyword=w,
                    keyword_type="keyword",
                    frequency=cnt,
                    tfidf_score=0.1,
                )
                for w, cnt in counter.most_common(top_n)
            ]

    def analyze_hashtags(
        self,
        hashtag_lists: List[List[str]],
        period_split_index: Optional[int] = None,
    ) -> List[KeywordItem]:
        """Aggregate hashtags, counts, and optional growth rates between periods."""
        if not hashtag_lists:
            return []

        all_tags = [tag for sublist in hashtag_lists for tag in sublist if tag]
        total_counts = Counter(all_tags)

        # Period-based growth rate if split index is given
        curr_counts: Counter[str] = Counter()
        prev_counts: Counter[str] = Counter()

        if period_split_index is not None and 0 < period_split_index < len(hashtag_lists):
            prev_tags = [t for sub in hashtag_lists[:period_split_index] for t in sub if t]
            curr_tags = [t for sub in hashtag_lists[period_split_index:] for t in sub if t]
            prev_counts = Counter(prev_tags)
            curr_counts = Counter(curr_tags)

        results: List[KeywordItem] = []
        for tag, total_freq in total_counts.most_common():
            growth = None
            if period_split_index is not None:
                c = curr_counts.get(tag, 0)
                p = prev_counts.get(tag, 0)
                if p > 0:
                    growth = round((c - p) / float(p), 4)
                elif c > 0:
                    growth = 1.0  # New emergence

            results.append(
                KeywordItem(
                    keyword=tag,
                    keyword_type="hashtag",
                    frequency=total_freq,
                    growth_rate=growth,
                )
            )

        return results
