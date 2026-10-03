"""Text cleaning and normalization for social media posts.

Implements canonical Phase 3 preprocessing policy:
- Preserves raw original_text
- Produces cleaned_text (lowercased, URLs removed, mentions removed, hashtag '#' stripped)
- Produces sentiment_ready_text (case-preserved, CardiffNLP style: @user, http)
- Provides deterministic runtime NER text derivation (case-preserved, clean)
- Extracts hashtags, mentions, URLs
- Hash-based duplicate tracking
- Fixed preprocessing_version = "1.0.0"
"""

import hashlib
import html
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set

PREPROCESSING_VERSION = "1.0.0"

# URL regex matching http, https, ftp, and www
URL_REGEX = re.compile(
    r"(?i)\b(?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’])",
    re.UNICODE,
)

# Mention regex (@username)
MENTION_REGEX = re.compile(r"(?<!\w)@([a-zA-Z0-9_]{1,50})\b", re.UNICODE)

# Hashtag regex (#hashtag)
HASHTAG_REGEX = re.compile(r"(?<!\w)#([a-zA-Z0-9_]+)\b", re.UNICODE)

# Excessive punctuation collapsing (e.g., !!!!!! -> !, ???? -> ?)
EXCESSIVE_PUNCT_REGEX = re.compile(r"([!?.,;])\1{2,}", re.UNICODE)

# Whitespace normalization regex
WHITESPACE_REGEX = re.compile(r"\s+", re.UNICODE)


@dataclass
class PreprocessedText:
    original_text: str
    cleaned_text: str
    sentiment_ready_text: str
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    is_duplicate: bool = False
    preprocessing_meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TextPreprocessor:
    """Canonical text preprocessor adhering to v1.0.0 specification."""

    def __init__(self, version: str = PREPROCESSING_VERSION):
        self.version = version

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract all URLs from text preserving order of first appearance."""
        urls = [m.group(0) for m in URL_REGEX.finditer(text)]
        # deduplicate while preserving order
        seen: Set[str] = set()
        deduped = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                deduped.append(u)
        return deduped

    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        """Extract all mention handles without @ symbol."""
        mentions = [m.group(1) for m in MENTION_REGEX.finditer(text)]
        seen: Set[str] = set()
        deduped = []
        for m in mentions:
            m_lower = m.lower()
            if m_lower not in seen:
                seen.add(m_lower)
                deduped.append(m)
        return deduped

    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        """Extract all hashtags without # symbol preserving original casing."""
        hashtags = [m.group(1) for m in HASHTAG_REGEX.finditer(text)]
        seen: Set[str] = set()
        deduped = []
        for tag in hashtags:
            tag_lower = tag.lower()
            if tag_lower not in seen:
                seen.add(tag_lower)
                deduped.append(tag)
        return deduped

    @staticmethod
    def decode_html_entities(text: str) -> str:
        """Decode HTML entities like &amp;, &lt;, &gt;, &quot;."""
        return html.unescape(text)

    @staticmethod
    def collapse_whitespace(text: str) -> str:
        """Collapse multiple spaces, newlines, and tabs into a single space."""
        return WHITESPACE_REGEX.sub(" ", text).strip()

    @staticmethod
    def collapse_punctuation(text: str) -> str:
        """Collapse excessive repeated punctuation (e.g. '!!!!!!' -> '!')."""
        return EXCESSIVE_PUNCT_REGEX.sub(r"\1", text)

    @staticmethod
    def compute_text_hash(text: str) -> str:
        """Compute SHA-256 hash of normalized text for deduplication."""
        normalized = WHITESPACE_REGEX.sub(" ", text.strip().lower())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def make_sentiment_ready(self, text: str) -> str:
        """Prepare text for CardiffNLP Twitter-RoBERTa sentiment classifier.

        - Preserves case
        - Converts @username -> @user
        - Converts URLs -> http
        - Decodes HTML entities
        - Collapses excessive punctuation
        - Collapses whitespace
        """
        if not text:
            return ""

        # Step 1: Decode HTML entities
        s = self.decode_html_entities(text)

        # Step 2: Replace mentions with @user
        s = MENTION_REGEX.sub("@user", s)

        # Step 3: Replace URLs with http
        s = URL_REGEX.sub("http", s)

        # Step 4: Collapse excessive punctuation
        s = self.collapse_punctuation(s)

        # Step 5: Collapse whitespace
        s = self.collapse_whitespace(s)

        return s

    def make_cleaned_text(self, text: str) -> str:
        """Prepare text for embeddings, BERTopic, TF-IDF, keywords, search.

        - Decodes HTML entities
        - Removes URLs
        - Removes @mentions
        - Strips '#' prefix from hashtags but keeps the token text
        - Collapses excessive punctuation
        - Normalizes whitespace
        - Lowercases
        """
        if not text:
            return ""

        # Step 1: Decode HTML entities
        s = self.decode_html_entities(text)

        # Step 2: Remove URLs
        s = URL_REGEX.sub(" ", s)

        # Step 3: Remove mentions
        s = MENTION_REGEX.sub(" ", s)

        # Step 4: Strip '#' from hashtags, keeping the token
        s = HASHTAG_REGEX.sub(r"\1", s)

        # Step 5: Collapse excessive punctuation
        s = self.collapse_punctuation(s)

        # Step 6: Collapse whitespace and lowercase
        s = self.collapse_whitespace(s).lower()

        return s

    @staticmethod
    def derive_ner_text(text: str) -> str:
        """Deterministic runtime derivation of case-preserved clean text for spaCy NER.

        - Decodes HTML entities
        - Removes URLs
        - Preserves casing
        - Strips '#' prefix from hashtags so named entities inside hashtags are recognizable
        - Retains @mentions or converts cleanly
        - Collapses whitespace
        """
        if not text:
            return ""

        s = html.unescape(text)
        s = URL_REGEX.sub(" ", s)
        s = HASHTAG_REGEX.sub(r"\1", s)
        s = EXCESSIVE_PUNCT_REGEX.sub(r"\1", s)
        s = WHITESPACE_REGEX.sub(" ", s).strip()
        return s

    def process(
        self,
        raw_text: Optional[str],
        seen_hashes: Optional[Set[str]] = None,
    ) -> PreprocessedText:
        """Process a single post's raw text and return canonical representations."""
        original = raw_text or ""

        # Extract features from original text
        urls = self.extract_urls(original)
        mentions = self.extract_mentions(original)
        hashtags = self.extract_hashtags(original)

        # Deduplication check
        text_hash = self.compute_text_hash(original)
        is_duplicate = False
        if seen_hashes is not None:
            if text_hash in seen_hashes:
                is_duplicate = True
            else:
                seen_hashes.add(text_hash)

        # Generate representations
        cleaned = self.make_cleaned_text(original)
        sentiment_ready = self.make_sentiment_ready(original)

        meta = {
            "version": self.version,
            "url_count": len(urls),
            "mention_count": len(mentions),
            "hashtag_count": len(hashtags),
            "char_length_original": len(original),
            "char_length_cleaned": len(cleaned),
            "text_hash": text_hash,
        }

        return PreprocessedText(
            original_text=original,
            cleaned_text=cleaned,
            sentiment_ready_text=sentiment_ready,
            hashtags=hashtags,
            mentions=mentions,
            urls=urls,
            is_duplicate=is_duplicate,
            preprocessing_meta=meta,
        )

    def process_batch(
        self,
        texts: List[str],
    ) -> List[PreprocessedText]:
        """Process a list of texts while tracking duplicates across the batch."""
        seen_hashes: Set[str] = set()
        results: List[PreprocessedText] = []
        for text in texts:
            result = self.process(text, seen_hashes=seen_hashes)
            results.append(result)
        return results
