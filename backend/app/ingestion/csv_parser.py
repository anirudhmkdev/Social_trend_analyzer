"""CSV parser with column auto-detection and file validation."""

from __future__ import annotations

import io
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, cast

import pandas as pd

# ---------------------------------------------------------------------------
# Column alias mapping: internal field → list of common source column names
# ---------------------------------------------------------------------------
COLUMN_ALIASES: Dict[str, List[str]] = {
    "text": [
        "text",
        "tweet",
        "tweet_text",
        "post",
        "body",
        "content",
        "message",
        "full_text",
        "post_text",
        "description",
        "status",
    ],
    "timestamp": [
        "timestamp",
        "created_at",
        "date",
        "datetime",
        "posted_at",
        "time",
        "published_at",
        "date_posted",
        "post_date",
    ],
    "platform": [
        "platform",
        "source",
        "network",
        "site",
        "service",
    ],
    "hashtags": [
        "hashtags",
        "tags",
        "hashtag",
        "hash_tags",
    ],
    "likes": [
        "likes",
        "like_count",
        "favorite_count",
        "favourites_count",
        "upvotes",
        "hearts",
        "reactions",
        "num_likes",
    ],
    "comments": [
        "comments",
        "comment_count",
        "reply_count",
        "replies",
        "num_comments",
        "num_replies",
    ],
    "shares": [
        "shares",
        "share_count",
        "retweet_count",
        "retweets",
        "reposts",
        "num_shares",
        "num_retweets",
    ],
    "author_id": [
        "author_id",
        "user_id",
        "username",
        "user",
        "screen_name",
        "user_screen_name",
        "author",
        "handle",
        "poster_id",
    ],
    "external_id": [
        "external_id",
        "id",
        "post_id",
        "tweet_id",
        "status_id",
        "message_id",
        "record_id",
    ],
}


@dataclass
class ColumnMapping:
    """Result of column auto-detection."""

    mappings: Dict[str, Optional[str]] = field(default_factory=dict)
    """Maps internal field name → source column name (None if not found)."""

    confidence: Dict[str, float] = field(default_factory=dict)
    """Confidence score per internal field (0.0–1.0)."""

    available_columns: List[str] = field(default_factory=list)
    """All columns present in the source CSV."""

    ambiguous_fields: List[str] = field(default_factory=list)
    """Fields with multiple plausible mappings (user should confirm)."""


@dataclass
class ParseResult:
    """Result of CSV parsing."""

    dataframe: pd.DataFrame
    """Raw DataFrame from the CSV."""

    column_mapping: ColumnMapping
    """Auto-detected column mappings."""

    total_rows: int = 0
    encoding_used: str = "utf-8"
    warnings: List[str] = field(default_factory=list)


def _normalize_col(name: str) -> str:
    """Normalize a column name for comparison (lowercase, strip, collapse spaces)."""
    return name.lower().strip().replace(" ", "_").replace("-", "_")


def _detect_column_mapping(columns: List[str]) -> ColumnMapping:
    """
    Auto-detect column mappings by comparing source column names against known aliases.

    Returns a ColumnMapping with best-guess mappings and confidence scores.
    """
    normalized_to_original: Dict[str, str] = {_normalize_col(c): c for c in columns}
    normalized_cols = list(normalized_to_original.keys())

    mappings: Dict[str, Optional[str]] = {}
    confidence: Dict[str, float] = {}
    ambiguous_fields: List[str] = []

    for internal_field, aliases in COLUMN_ALIASES.items():
        matches: List[Tuple[str, float]] = []

        for alias in aliases:
            alias_norm = _normalize_col(alias)
            if alias_norm in normalized_cols:
                # Exact normalized match
                idx = aliases.index(alias)
                # Higher confidence for early aliases (more canonical names)
                conf = 1.0 - (idx * 0.05)
                conf = max(conf, 0.5)
                matches.append((normalized_to_original[alias_norm], conf))

        if len(matches) == 0:
            mappings[internal_field] = None
            confidence[internal_field] = 0.0
        elif len(matches) == 1:
            mappings[internal_field] = matches[0][0]
            confidence[internal_field] = matches[0][1]
        else:
            # Multiple matches — pick highest confidence, flag as ambiguous
            best = max(matches, key=lambda x: x[1])
            mappings[internal_field] = best[0]
            confidence[internal_field] = best[1]
            if internal_field in ("text", "timestamp"):
                # Only flag required fields as ambiguous
                ambiguous_fields.append(internal_field)

    return ColumnMapping(
        mappings=mappings,
        confidence=confidence,
        available_columns=columns,
        ambiguous_fields=ambiguous_fields,
    )


def _try_read_csv(content: bytes) -> Tuple[pd.DataFrame, str]:
    """
    Attempt to read CSV content, trying multiple encodings.

    Returns (DataFrame, encoding_used). Raises ValueError on failure.
    """
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]
    last_error: Optional[Exception] = None

    for enc in encodings:
        try:
            df = pd.read_csv(io.BytesIO(content), encoding=enc, low_memory=False)
            return df, enc
        except (UnicodeDecodeError, pd.errors.ParserError) as exc:
            last_error = exc
            continue

    raise ValueError(f"Unable to parse CSV with encodings {encodings}. Last error: {last_error}")


def parse_csv(
    content: bytes,
    filename: str = "upload.csv",
    max_size_mb: int = 50,
) -> ParseResult:
    """
    Parse raw CSV bytes into a DataFrame with auto-detected column mappings.

    Args:
        content: Raw CSV file bytes.
        filename: Original filename (used only for validation messages).
        max_size_mb: Maximum allowed file size in MB.

    Returns:
        ParseResult with DataFrame and column mapping.

    Raises:
        ValueError: If the file is invalid, too large, empty, or unparseable.
    """
    # --- Size validation ---
    size_mb = len(content) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValueError(
            f"File size {size_mb:.1f} MB exceeds the maximum allowed {max_size_mb} MB."
        )

    if len(content) == 0:
        raise ValueError("Uploaded file is empty.")

    # --- Extension check ---
    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".csv",):
        raise ValueError(f"Unsupported file extension '{ext}'. Only .csv files are accepted.")

    # --- Parse ---
    warnings: List[str] = []
    try:
        df, encoding = _try_read_csv(content)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    if df.empty:
        raise ValueError("The uploaded CSV file contains no data rows.")

    if len(df.columns) == 0:
        raise ValueError("The CSV file contains no columns.")

    # --- Drop fully empty rows ---
    initial_rows = len(df)
    df = df.dropna(how="all")
    if len(df) < initial_rows:
        warnings.append(f"Dropped {initial_rows - len(df)} fully-empty rows from the CSV.")

    if len(df) == 0:
        raise ValueError("All rows in the CSV are empty.")

    # --- Column name sanitization ---
    df.columns = [str(c).strip() for c in df.columns]

    # --- Detect column mappings ---
    mapping = _detect_column_mapping(list(df.columns))

    return ParseResult(
        dataframe=df,
        column_mapping=mapping,
        total_rows=len(df),
        encoding_used=encoding,
        warnings=warnings,
    )


def apply_column_mapping(
    df: pd.DataFrame,
    mapping: Dict[str, Optional[str]],
) -> pd.DataFrame:
    """
    Rename source columns to internal field names based on the provided mapping.

    Only mapped columns are kept in the resulting DataFrame.
    All unmapped source columns are discarded.

    Args:
        df: Source DataFrame.
        mapping: Dict mapping internal field names → source column names.

    Returns:
        DataFrame with columns renamed to internal field names.
    """
    rename_map: Dict[str, str] = {}
    keep_cols: List[str] = []

    for internal_name, source_col in mapping.items():
        if source_col is not None and source_col in df.columns:
            rename_map[source_col] = internal_name
            keep_cols.append(source_col)

    # Keep only mapped columns, rename them
    result = df[keep_cols].rename(columns=rename_map)
    return result


def get_csv_preview(df: pd.DataFrame, n_rows: int = 20) -> List[Dict[str, Any]]:
    """Return the first n_rows of a DataFrame as a list of row dicts."""
    preview_df = df.head(n_rows).copy()
    # Replace NaN with None for JSON serialization
    preview_df = preview_df.where(pd.notnull(preview_df), None)
    return cast(List[Dict[str, Any]], preview_df.to_dict(orient="records"))
