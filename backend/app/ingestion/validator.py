"""Data validator: validates parsed DataFrames before normalization."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.ingestion.timestamp_parser import parse_timestamp


@dataclass
class ValidationIssue:
    """A single validation issue for a row."""

    row_index: int
    issue_type: str
    detail: str


@dataclass
class ValidationResult:
    """Summary of dataset validation results."""

    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    missing_text: int = 0
    missing_timestamp: int = 0
    invalid_timestamp: int = 0
    duplicate_rows: int = 0
    missing_author_id: int = 0
    date_range_earliest: Optional[str] = None
    date_range_latest: Optional[str] = None
    platform_distribution: Dict[str, int] = field(default_factory=dict)
    missing_optional_fields: Dict[str, int] = field(default_factory=dict)
    issues: List[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "invalid_rows": self.invalid_rows,
            "issues": {
                "missing_text": self.missing_text,
                "missing_timestamp": self.missing_timestamp,
                "invalid_timestamp": self.invalid_timestamp,
                "duplicate_posts": self.duplicate_rows,
            },
            "date_range": {
                "earliest": self.date_range_earliest,
                "latest": self.date_range_latest,
            },
            "platform_distribution": self.platform_distribution,
            "missing_field_counts": self.missing_optional_fields,
            "row_issues": [asdict(issue) for issue in self.issues[:200]],
            "issues_truncated": len(self.issues) > 200,
        }


def validate_dataset(
    df: pd.DataFrame,
    column_mapping: Dict[str, Optional[str]],
    min_text_length: int = 3,
) -> Tuple[ValidationResult, pd.DataFrame]:
    """
    Validate a mapped DataFrame against ingestion rules.

    Args:
        df: DataFrame with internal field names (already mapped).
        column_mapping: The mapping used (to detect missing engagement fields).
        min_text_length: Minimum text length to consider a post valid.

    Returns:
        (ValidationResult, valid_rows_df) where valid_rows_df is the subset
        of rows that passed validation.
    """
    result = ValidationResult(total_rows=len(df))
    invalid_indices: set = set()
    seen_hashes: set = set()
    duplicate_indices: set = set()

    # Build text hash for deduplication
    text_col_present = "text" in df.columns
    timestamp_col_present = "timestamp" in df.columns

    # --- Row-level validation ---
    for idx, row in df.iterrows():
        row_invalid = False

        # 1. Missing / empty text
        if not text_col_present:
            row_invalid = True
            result.missing_text += 1
        else:
            text_val = row.get("text", None)
            if pd.isna(text_val) or str(text_val).strip() == "":
                row_invalid = True
                result.missing_text += 1
                result.issues.append(
                    ValidationIssue(int(str(idx)), "missing_text", "Text field is empty")
                )
            elif len(str(text_val).strip()) < min_text_length:
                row_invalid = True
                result.missing_text += 1
                result.issues.append(
                    ValidationIssue(
                        int(str(idx)),
                        "missing_text",
                        f"Text too short ("
                        f"{len(str(text_val).strip())} chars, min {min_text_length})",
                    )
                )

        # 2. Missing / invalid timestamp
        if not timestamp_col_present:
            row_invalid = True
            result.missing_timestamp += 1
        else:
            ts_val = row.get("timestamp", None)
            if pd.isna(ts_val) or str(ts_val).strip() == "":
                row_invalid = True
                result.missing_timestamp += 1
                result.issues.append(
                    ValidationIssue(int(str(idx)), "missing_timestamp", "Timestamp is empty")
                )
            else:
                parsed_ts = parse_timestamp(str(ts_val))
                if parsed_ts is None:
                    row_invalid = True
                    result.invalid_timestamp += 1
                    result.issues.append(
                        ValidationIssue(
                            int(str(idx)),
                            "invalid_timestamp",
                            f"Cannot parse timestamp: '{ts_val}'",
                        )
                    )

        if row_invalid:
            invalid_indices.add(idx)

    # 3. Duplicate detection (by text hash)
    if text_col_present:
        for idx, row in df.iterrows():
            if idx in invalid_indices:
                continue
            text_val = str(row.get("text", "")).strip()
            text_hash = hashlib.md5(text_val.encode("utf-8")).hexdigest()
            if text_hash in seen_hashes:
                duplicate_indices.add(idx)
                result.duplicate_rows += 1
                result.issues.append(
                    ValidationIssue(
                        int(str(idx)), "duplicate", "Repeated text; retained and flagged"
                    )
                )
            else:
                seen_hashes.add(text_hash)

    # --- Date range ---
    valid_timestamps: List[datetime] = []
    if timestamp_col_present:
        for idx, row in df.iterrows():
            if idx in invalid_indices:
                continue
            ts_val = row.get("timestamp", None)
            if not pd.isna(ts_val):
                parsed_ts = parse_timestamp(str(ts_val))
                if parsed_ts is not None:
                    valid_timestamps.append(parsed_ts)

    if valid_timestamps:
        result.date_range_earliest = min(valid_timestamps).isoformat()
        result.date_range_latest = max(valid_timestamps).isoformat()

    # --- Platform distribution ---
    if "platform" in df.columns:
        platform_counts = (
            df.loc[~df.index.isin(invalid_indices), "platform"]
            .dropna()
            .astype(str)
            .value_counts()
            .to_dict()
        )
        result.platform_distribution = {str(k): int(v) for k, v in platform_counts.items()}

    # --- Missing optional fields ---
    optional_fields = ["hashtags", "likes", "comments", "shares", "author_id", "external_id"]
    for f in optional_fields:
        if f not in df.columns:
            result.missing_optional_fields[f] = len(df)
        else:
            missing_count = int(df[f].isna().sum())
            if missing_count > 0:
                result.missing_optional_fields[f] = missing_count

    # --- Compute final counts ---
    all_invalid = invalid_indices  # duplicates are flagged but not removed
    result.invalid_rows = len(all_invalid)
    result.valid_rows = result.total_rows - result.invalid_rows

    # --- Filter to valid rows only ---
    valid_df = df.loc[~df.index.isin(all_invalid)].copy()
    # Mark duplicates
    if "is_duplicate" not in valid_df.columns:
        valid_df["is_duplicate"] = False
    valid_df.loc[valid_df.index.isin(duplicate_indices), "is_duplicate"] = True

    return result, valid_df
