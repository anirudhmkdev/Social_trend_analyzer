"""Data normalizer: converts validated DataFrame rows into Post ORM objects."""

from __future__ import annotations

import re
from datetime import timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import pandas as pd

from app.ingestion.timestamp_parser import parse_timestamp

# Hashtag extraction regex
_HASHTAG_RE = re.compile(r"#(\w+)")
# Mention extraction regex
_MENTION_RE = re.compile(r"@(\w+)")
# URL extraction regex (simplified but functional)
_URL_RE = re.compile(
    r"https?://[^\s<>\"{}|\\^`\[\]]*",
    re.IGNORECASE,
)


def _extract_hashtags(text: str) -> List[str]:
    """Extract hashtag terms from text (without the # prefix)."""
    return [m.lower() for m in _HASHTAG_RE.findall(text)]


def _extract_mentions(text: str) -> List[str]:
    """Extract @mention handles from text (without the @ prefix)."""
    return _MENTION_RE.findall(text)


def _extract_urls(text: str) -> List[str]:
    """Extract URLs from text."""
    return _URL_RE.findall(text)


def _safe_int(val: Any) -> Optional[int]:
    """Convert a value to int, returning None on failure."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        value = float(str(val))
        return int(value) if 0 <= value <= 2_147_483_647 and value.is_integer() else None
    except (ValueError, TypeError, OverflowError):
        return None


def normalize_row(
    row: Dict[str, Any],
    dataset_id: UUID,
    column_mapping: Dict[str, Optional[str]],
) -> Optional[Dict[str, Any]]:
    """
    Normalize a single mapped row dict into a Post-compatible dict.

    Returns None if the row cannot be normalized (missing required fields).

    Notes on engagement:
    - If a column was NOT mapped (column_mapping[field] is None), engagement
      value should be stored as NULL (Python None) — field was unavailable.
    - If a column WAS mapped but value is 0, store 0 — genuine zero engagement.
    """
    # --- Required: text ---
    text_val = row.get("text", None)
    if text_val is None or (isinstance(text_val, float) and pd.isna(text_val)):
        return None
    original_text = str(text_val)
    if not original_text.strip():
        return None

    # --- Required: timestamp ---
    ts_val = row.get("timestamp", None)
    if ts_val is None or (isinstance(ts_val, float) and pd.isna(ts_val)):
        return None
    parsed_ts = parse_timestamp(str(ts_val))
    if parsed_ts is None:
        return None
    # Ensure UTC-aware
    if parsed_ts.tzinfo is None:
        parsed_ts = parsed_ts.replace(tzinfo=timezone.utc)

    # --- Optional: platform ---
    platform_val = row.get("platform", None)
    platform: Optional[str] = None
    if platform_val is not None and not (isinstance(platform_val, float) and pd.isna(platform_val)):
        platform = str(platform_val).strip().lower() or None

    # --- Optional: hashtags ---
    # Prefer mapped hashtag column, fall back to extraction from text
    hashtags_val = row.get("hashtags", None)
    hashtags: List[str] = []
    if hashtags_val is not None and not (isinstance(hashtags_val, float) and pd.isna(hashtags_val)):
        raw_ht = str(hashtags_val)
        # The field may contain comma-separated hashtags, or be JSON-like
        hashtags = [h.strip().lstrip("#").lower() for h in re.split(r"[,|;]", raw_ht) if h.strip()]
    # Always also extract from text (deduplicated)
    text_hashtags = _extract_hashtags(original_text)
    for ht in text_hashtags:
        if ht not in hashtags:
            hashtags.append(ht)

    # --- Optional: engagement ---
    # Distinguish between "column not mapped" (None) vs "column mapped but value is 0"
    def get_engagement(field: str) -> Optional[int]:
        if column_mapping.get(field) is None:
            return None  # Column not mapped → unavailable
        val = row.get(field, None)
        return _safe_int(val)

    likes = get_engagement("likes")
    comments = get_engagement("comments")
    shares = get_engagement("shares")

    # --- Optional: author_id ---
    author_val = row.get("author_id", None)
    author_id: Optional[str] = None
    if author_val is not None and not (isinstance(author_val, float) and pd.isna(author_val)):
        author_id = str(author_val).strip() or None

    # --- Optional: external_id ---
    ext_val = row.get("external_id", None)
    external_id: Optional[str] = None
    if ext_val is not None and not (isinstance(ext_val, float) and pd.isna(ext_val)):
        external_id = str(ext_val).strip() or None

    # --- Side-channel extractions from text ---
    mentions = _extract_mentions(original_text)
    urls = _extract_urls(original_text)

    # --- is_duplicate ---
    is_duplicate = bool(row.get("is_duplicate", False))

    return {
        "dataset_id": dataset_id,
        "external_id": external_id,
        "original_text": original_text,
        "cleaned_text": None,  # Set during preprocessing phase
        "sentiment_ready_text": None,  # Set during preprocessing phase
        "timestamp": parsed_ts,
        "platform": platform,
        "hashtags": hashtags if hashtags else None,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "author_id": author_id,
        "mentions": mentions if mentions else None,
        "urls": urls if urls else None,
        "is_duplicate": is_duplicate,
        "preprocessing_meta": None,
    }


def normalize_dataframe(
    df: pd.DataFrame,
    dataset_id: UUID,
    column_mapping: Dict[str, Optional[str]],
) -> List[Dict[str, Any]]:
    """
    Normalize all rows in a mapped DataFrame into Post dicts.

    Rows that fail normalization are silently skipped (they should have been
    caught during validation).

    Returns list of Post-compatible dicts.
    """
    posts: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        row_dict = row.where(pd.notnull(row), None).to_dict()
        normalized = normalize_row(row_dict, dataset_id, column_mapping)
        if normalized is not None:
            posts.append(normalized)
    return posts
