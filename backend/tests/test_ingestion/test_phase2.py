"""Tests for CSV parser, column detection, validator, normalizer, and dataset API."""

from __future__ import annotations

import csv
import io

import pytest

from app.ingestion.csv_parser import _detect_column_mapping, parse_csv
from app.ingestion.normalizer import normalize_row
from app.ingestion.sample_generator import generate_sample_dataset
from app.ingestion.timestamp_parser import parse_timestamp
from app.ingestion.validator import validate_dataset

# ---------------------------------------------------------------------------
# Timestamp parser tests
# ---------------------------------------------------------------------------


def test_parse_iso8601_utc() -> None:
    dt = parse_timestamp("2026-07-15T14:30:00Z")
    assert dt is not None
    assert dt.tzinfo is not None
    assert dt.year == 2026
    assert dt.month == 7
    assert dt.day == 15


def test_parse_iso8601_with_offset() -> None:
    dt = parse_timestamp("2026-07-15T10:30:00-04:00")
    assert dt is not None
    # Should normalize to UTC: 10:30 + 4h = 14:30
    assert dt.hour == 14


def test_parse_unix_timestamp() -> None:
    dt = parse_timestamp("1721051400")
    assert dt is not None
    assert dt.tzinfo is not None


def test_parse_unix_milliseconds() -> None:
    dt = parse_timestamp("1721051400000")
    assert dt is not None


def test_parse_date_only() -> None:
    dt = parse_timestamp("2026-07-15")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 7


def test_parse_invalid_timestamp() -> None:
    dt = parse_timestamp("not-a-date")
    assert dt is None


def test_parse_empty_timestamp() -> None:
    dt = parse_timestamp("")
    assert dt is None


# ---------------------------------------------------------------------------
# Column detection tests
# ---------------------------------------------------------------------------


def test_detect_text_column() -> None:
    mapping = _detect_column_mapping(["tweet_text", "created_at", "likes"])
    assert mapping.mappings["text"] == "tweet_text"
    assert mapping.confidence["text"] > 0


def test_detect_timestamp_column() -> None:
    mapping = _detect_column_mapping(["body", "created_at", "platform"])
    assert mapping.mappings["timestamp"] == "created_at"


def test_detect_engagement_columns() -> None:
    cols = ["text", "date", "favorite_count", "reply_count", "retweet_count"]
    mapping = _detect_column_mapping(cols)
    assert mapping.mappings["likes"] == "favorite_count"
    assert mapping.mappings["comments"] == "reply_count"
    assert mapping.mappings["shares"] == "retweet_count"


def test_detect_no_match() -> None:
    mapping = _detect_column_mapping(["col_a", "col_b"])
    assert mapping.mappings["text"] is None
    assert mapping.mappings["timestamp"] is None


# ---------------------------------------------------------------------------
# CSV parser tests
# ---------------------------------------------------------------------------


def make_csv_bytes(rows: list[dict], fieldnames: list[str] | None = None) -> bytes:
    """Helper to create CSV bytes from a list of dicts."""
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def test_parse_valid_csv() -> None:
    content = make_csv_bytes(
        [
            {"text": "Hello world", "created_at": "2026-07-01T12:00:00Z", "platform": "twitter"},
            {"text": "Another post", "created_at": "2026-07-02T09:30:00Z", "platform": "reddit"},
        ]
    )
    result = parse_csv(content, "test.csv")
    assert result.total_rows == 2
    assert (
        "text" in result.column_mapping.mappings
        or "created_at" in result.column_mapping.available_columns
    )


def test_parse_empty_file() -> None:
    with pytest.raises(ValueError, match="empty"):
        parse_csv(b"", "test.csv")


def test_parse_wrong_extension() -> None:
    with pytest.raises(ValueError, match="extension"):
        parse_csv(b"col\nval", "test.json")


def test_parse_file_too_large() -> None:
    big_content = b"text,ts\n" + b"hello,2026-01-01\n" * 10
    with pytest.raises(ValueError, match="size"):
        parse_csv(big_content, "test.csv", max_size_mb=0)


# ---------------------------------------------------------------------------
# Validator tests
# ---------------------------------------------------------------------------


def test_validator_valid_rows() -> None:
    import pandas as pd

    df = pd.DataFrame(
        [
            {"text": "Hello world", "timestamp": "2026-07-01T12:00:00Z"},
            {"text": "Another post", "timestamp": "2026-07-02T09:30:00Z"},
        ]
    )
    mapping = {"text": "text", "timestamp": "timestamp"}
    result, valid_df = validate_dataset(df, mapping)
    assert result.total_rows == 2
    assert result.valid_rows == 2
    assert result.invalid_rows == 0


def test_validator_missing_text() -> None:
    import pandas as pd

    df = pd.DataFrame(
        [
            {"text": None, "timestamp": "2026-07-01T12:00:00Z"},
            {"text": "Valid post", "timestamp": "2026-07-02T09:30:00Z"},
        ]
    )
    mapping = {"text": "text", "timestamp": "timestamp"}
    result, valid_df = validate_dataset(df, mapping)
    assert result.missing_text == 1
    assert result.valid_rows == 1


def test_validator_invalid_timestamp() -> None:
    import pandas as pd

    df = pd.DataFrame(
        [
            {"text": "Hello", "timestamp": "not-a-date"},
            {"text": "Valid", "timestamp": "2026-07-01T12:00:00Z"},
        ]
    )
    mapping = {"text": "text", "timestamp": "timestamp"}
    result, valid_df = validate_dataset(df, mapping)
    assert result.invalid_timestamp == 1


def test_validator_duplicates() -> None:
    import pandas as pd

    df = pd.DataFrame(
        [
            {"text": "Same post", "timestamp": "2026-07-01T12:00:00Z"},
            {"text": "Same post", "timestamp": "2026-07-02T09:30:00Z"},
            {"text": "Unique post", "timestamp": "2026-07-03T08:00:00Z"},
        ]
    )
    mapping = {"text": "text", "timestamp": "timestamp"}
    result, valid_df = validate_dataset(df, mapping)
    assert result.duplicate_rows == 1


# ---------------------------------------------------------------------------
# Normalizer tests
# ---------------------------------------------------------------------------


def test_normalize_basic_row() -> None:
    import uuid

    dataset_id = uuid.uuid4()
    row = {
        "text": "Hello #world @user",
        "timestamp": "2026-07-01T12:00:00Z",
        "platform": "twitter",
        "likes": "42",
        "comments": "5",
        "shares": "10",
    }
    mapping = {
        "text": "text",
        "timestamp": "timestamp",
        "platform": "platform",
        "likes": "likes",
        "comments": "comments",
        "shares": "shares",
        "hashtags": None,
        "author_id": None,
        "external_id": None,
    }
    result = normalize_row(row, dataset_id, mapping)
    assert result is not None
    assert result["original_text"] == "Hello #world @user"
    assert result["platform"] == "twitter"
    assert result["likes"] == 42
    assert "world" in (result["hashtags"] or [])


def test_normalize_missing_text_returns_none() -> None:
    import uuid

    dataset_id = uuid.uuid4()
    row = {"text": None, "timestamp": "2026-07-01T12:00:00Z"}
    mapping = {"text": "text", "timestamp": "timestamp", "likes": None}
    result = normalize_row(row, dataset_id, mapping)
    assert result is None


def test_normalize_engagement_unavailable_vs_zero() -> None:
    """Unmapped engagement field → None. Mapped field with 0 → 0."""
    import uuid

    dataset_id = uuid.uuid4()
    # Engagement columns not mapped
    row = {"text": "Post", "timestamp": "2026-07-01T12:00:00Z", "likes": 0}
    mapping_no_likes = {
        "text": "text",
        "timestamp": "timestamp",
        "likes": None,  # NOT mapped
        "comments": None,
        "shares": None,
        "hashtags": None,
        "author_id": None,
        "external_id": None,
        "platform": None,
    }
    result_no = normalize_row(row, dataset_id, mapping_no_likes)
    assert result_no is not None
    assert result_no["likes"] is None  # field not mapped → NULL

    # Engagement mapped but value is 0
    mapping_with_likes = {**mapping_no_likes, "likes": "likes"}
    result_with = normalize_row(row, dataset_id, mapping_with_likes)
    assert result_with is not None
    assert result_with["likes"] == 0  # genuine zero engagement


# ---------------------------------------------------------------------------
# Sample dataset tests
# ---------------------------------------------------------------------------


def test_sample_dataset_generation() -> None:
    csv_content = generate_sample_dataset()
    lines = csv_content.strip().split("\n")
    # Should have header + at least 500 rows
    assert len(lines) > 500
    # Header should contain required fields
    header = lines[0]
    assert "text" in header
    assert "created_at" in header
    assert "platform" in header


def test_sample_dataset_deterministic() -> None:
    csv1 = generate_sample_dataset(seed=42)
    csv2 = generate_sample_dataset(seed=42)
    assert csv1 == csv2


# ---------------------------------------------------------------------------
# Dataset API integration tests
# ---------------------------------------------------------------------------


def test_load_sample_dataset(client: object) -> None:
    """Test loading sample dataset via API."""
    response = client.post("/api/v1/datasets/sample")  # type: ignore[attr-defined]
    assert response.status_code == 201
    data = response.json()
    assert "dataset_id" in data
    assert data["row_count"] > 0


def test_list_datasets(client: object) -> None:
    """After loading sample, listing should return it."""
    client.post("/api/v1/datasets/sample")  # type: ignore[attr-defined]
    response = client.get("/api/v1/datasets")  # type: ignore[attr-defined]
    assert response.status_code == 200
    data = response.json()
    assert "datasets" in data
    assert data["total"] >= 1


def test_get_dataset_not_found(client: object) -> None:
    """Non-existent dataset should return 404."""
    response = client.get("/api/v1/datasets/00000000-0000-0000-0000-000000000000")  # type: ignore[attr-defined]
    assert response.status_code == 404


def test_upload_csv_valid(client: object) -> None:
    """Test uploading a valid CSV file."""
    csv_content = make_csv_bytes(
        [
            {"text": "Test post 1", "created_at": "2026-07-01T12:00:00Z"},
            {"text": "Test post 2", "created_at": "2026-07-02T12:00:00Z"},
        ]
    )
    response = client.post(  # type: ignore[attr-defined]
        "/api/v1/datasets/upload",
        files={"file": ("test.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["row_count"] == 2


def test_upload_csv_empty(client: object) -> None:
    """Empty file should return 422."""
    response = client.post(  # type: ignore[attr-defined]
        "/api/v1/datasets/upload",
        files={"file": ("empty.csv", b"", "text/csv")},
    )
    assert response.status_code == 422


def test_upload_wrong_extension(client: object) -> None:
    """Non-CSV file should return 422."""
    response = client.post(  # type: ignore[attr-defined]
        "/api/v1/datasets/upload",
        files={"file": ("data.json", b'{"key": "val"}', "application/json")},
    )
    assert response.status_code == 422


def test_delete_dataset(client: object) -> None:
    """Test deleting a dataset."""
    # First create one
    csv_content = make_csv_bytes(
        [
            {"text": "Post to delete", "created_at": "2026-07-01T12:00:00Z"},
        ]
    )
    create_response = client.post(  # type: ignore[attr-defined]
        "/api/v1/datasets/upload",
        files={"file": ("del.csv", csv_content, "text/csv")},
    )
    dataset_id = create_response.json()["id"]

    # Delete it
    del_response = client.delete(f"/api/v1/datasets/{dataset_id}")  # type: ignore[attr-defined]
    assert del_response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/api/v1/datasets/{dataset_id}")  # type: ignore[attr-defined]
    assert get_response.status_code == 404
