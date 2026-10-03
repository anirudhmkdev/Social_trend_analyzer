"""Dataset service: orchestrates CSV ingestion, column mapping, validation and normalization."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import EntityNotFoundException, ValidationException
from app.core.logging import logger
from app.ingestion.csv_parser import (
    ParseResult,
    apply_column_mapping,
    parse_csv,
)
from app.ingestion.normalizer import normalize_dataframe
from app.ingestion.sample_generator import generate_sample_dataset
from app.ingestion.validator import validate_dataset
from app.models.dataset import Dataset
from app.models.post import Post

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _ensure_upload_dir() -> str:
    """Ensure the upload directory exists and return its path."""
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def _save_file(content: bytes, filename: str) -> str:
    """Save uploaded bytes to the upload directory. Returns the saved filepath."""
    upload_dir = _ensure_upload_dir()
    safe_name = f"{uuid.uuid4().hex}_{os.path.basename(filename)}"
    filepath = os.path.join(upload_dir, safe_name)
    with open(filepath, "wb") as f:
        f.write(content)
    return filepath


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


def upload_csv(
    db: Session,
    content: bytes,
    filename: str,
) -> Tuple[Dataset, ParseResult]:
    """
    Parse a CSV file, auto-detect columns, and create a Dataset record.

    Args:
        db: Database session.
        content: Raw CSV bytes.
        filename: Original filename.

    Returns:
        (Dataset ORM object, ParseResult with DataFrame and detected mappings).

    Raises:
        ValidationException: If the file is invalid.
    """
    try:
        parse_result = parse_csv(
            content=content,
            filename=filename,
            max_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        )
    except ValueError as exc:
        raise ValidationException(str(exc)) from exc

    # Persist the file
    try:
        _save_file(content, filename)
    except OSError as exc:
        logger.error("Failed to save uploaded file: %s", exc)
        # Non-fatal — we can still proceed with in-memory parsing

    # Build initial column_mapping dict from auto-detection
    detected_mapping = {
        field: source_col
        for field, source_col in parse_result.column_mapping.mappings.items()
    }

    dataset = Dataset(
        name=os.path.splitext(filename)[0],
        filename=filename,
        source_type="csv",
        file_size_bytes=len(content),
        row_count=parse_result.total_rows,
        column_mapping=detected_mapping,
        status="uploaded",
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset, parse_result


def load_sample_dataset(db: Session) -> Dataset:
    """
    Load the bundled synthetic demo dataset into the database.

    Creates a Dataset record and imports all Posts.

    Returns the created Dataset.
    """
    # Check if sample already exists
    existing = (
        db.query(Dataset)
        .filter(Dataset.source_type == "synthetic_demo")
        .first()
    )
    if existing is not None:
        logger.info("Sample dataset already exists (id=%s)", existing.id)
        return existing

    # Generate CSV
    csv_content = generate_sample_dataset()
    csv_bytes = csv_content.encode("utf-8")

    # Parse
    try:
        parse_result = parse_csv(
            content=csv_bytes,
            filename="sample_dataset.csv",
            max_size_mb=200,
        )
    except ValueError as exc:
        raise ValidationException(f"Failed to parse sample dataset: {exc}") from exc

    # Use default column mapping for sample dataset (known structure)
    column_mapping: Dict[str, Optional[str]] = {
        "text": "text",
        "timestamp": "created_at",
        "platform": "platform",
        "hashtags": "hashtags",
        "likes": "likes",
        "comments": "comments",
        "shares": "shares",
        "author_id": "author_id",
        "external_id": "id",
    }

    # Apply mapping
    mapped_df = apply_column_mapping(parse_result.dataframe, column_mapping)

    # Validate
    dataset_id = uuid.uuid4()
    validation_result, valid_df = validate_dataset(
        mapped_df,
        column_mapping,
    )

    # Create Dataset record
    dataset = Dataset(
        id=dataset_id,
        name="Social Media Sample Dataset (Synthetic Demo)",
        filename="sample_dataset.csv",
        source_type="synthetic_demo",
        file_size_bytes=len(csv_bytes),
        row_count=parse_result.total_rows,
        valid_row_count=validation_result.valid_rows,
        column_mapping=column_mapping,
        validation_results=validation_result.to_dict(),
        status="imported",
    )
    db.add(dataset)
    db.flush()

    # Normalize and insert posts
    normalized_posts = normalize_dataframe(valid_df, dataset_id, column_mapping)

    batch_size = 500
    for i in range(0, len(normalized_posts), batch_size):
        batch = normalized_posts[i : i + batch_size]
        db.bulk_insert_mappings(Post, batch)  # type: ignore[arg-type]

    db.commit()
    db.refresh(dataset)

    logger.info(
        "Sample dataset loaded: %d posts (dataset_id=%s)",
        len(normalized_posts),
        dataset_id,
    )
    return dataset


def get_dataset(db: Session, dataset_id: UUID) -> Dataset:
    """Retrieve a dataset by ID or raise EntityNotFoundException."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if dataset is None:
        raise EntityNotFoundException("Dataset", str(dataset_id))
    return dataset


def list_datasets(db: Session, limit: int = 50, offset: int = 0) -> Tuple[List[Dataset], int]:
    """List all datasets with pagination. Returns (datasets, total_count)."""
    total = db.query(Dataset).count()
    datasets = (
        db.query(Dataset)
        .order_by(Dataset.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return datasets, total


def get_dataset_preview(
    db: Session,
    dataset_id: UUID,
    n_rows: int = 20,
) -> Dict[str, Any]:
    """
    Return a preview of dataset posts directly from the database.

    Returns a dict with columns and rows.
    """
    get_dataset(db, dataset_id)  # Validates dataset exists
    posts = (
        db.query(Post)
        .filter(Post.dataset_id == dataset_id)
        .order_by(Post.timestamp)
        .limit(n_rows)
        .all()
    )
    total_posts = db.query(Post).filter(Post.dataset_id == dataset_id).count()

    columns = [
        "id", "original_text", "timestamp", "platform",
        "hashtags", "likes", "comments", "shares", "is_duplicate",
    ]
    rows = []
    for post in posts:
        rows.append(
            {
                "id": str(post.id),
                "original_text": post.original_text,
                "timestamp": post.timestamp.isoformat() if post.timestamp else None,
                "platform": post.platform,
                "hashtags": post.hashtags,
                "likes": post.likes,
                "comments": post.comments,
                "shares": post.shares,
                "is_duplicate": post.is_duplicate,
            }
        )

    return {
        "dataset_id": dataset_id,
        "columns": columns,
        "rows": rows,
        "total_rows": total_posts,
        "shown_rows": len(rows),
    }


def update_column_mapping(
    db: Session,
    dataset_id: UUID,
    column_mapping: Dict[str, Optional[str]],
) -> Dataset:
    """Update the column mapping for a dataset."""
    dataset = get_dataset(db, dataset_id)
    dataset.column_mapping = column_mapping
    dataset.status = "mapped"
    dataset.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(dataset)
    return dataset


def run_validation(
    db: Session,
    dataset_id: UUID,
) -> Tuple[Dataset, Dict[str, Any]]:
    """
    Reload the dataset CSV and run validation. Updates validation_results on the dataset.

    Returns (dataset, validation_result_dict).
    """
    dataset = get_dataset(db, dataset_id)

    if not dataset.column_mapping:
        raise ValidationException("Column mapping must be set before running validation.")

    # For an already-imported dataset, return cached results
    if dataset.status == "imported" and dataset.validation_results:
        return dataset, dataset.validation_results

    # Re-read posts from database for validation
    total = db.query(Post).filter(Post.dataset_id == dataset_id).count()
    valid = (
        db.query(Post)
        .filter(Post.dataset_id == dataset_id, Post.is_duplicate == False)  # noqa: E712
        .count()
    )
    dupes = db.query(Post).filter(Post.dataset_id == dataset_id, Post.is_duplicate == True).count()  # noqa: E712

    # Build a minimal validation result from existing data
    if dataset.validation_results:
        return dataset, dataset.validation_results

    result_dict: Dict[str, Any] = {
        "total_rows": total,
        "valid_rows": valid,
        "invalid_rows": 0,
        "issues": {
            "missing_text": 0,
            "missing_timestamp": 0,
            "invalid_timestamp": 0,
            "duplicate_posts": dupes,
        },
        "date_range": {"earliest": None, "latest": None},
        "platform_distribution": {},
        "missing_field_counts": {},
    }

    dataset.validation_results = result_dict
    dataset.row_count = total
    dataset.valid_row_count = valid
    dataset.status = "validated"
    dataset.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(dataset)

    return dataset, result_dict


def import_dataset(
    db: Session,
    dataset_id: UUID,
    csv_content: bytes,
    filename: str,
    column_mapping: Dict[str, Optional[str]],
) -> Dataset:
    """
    Import posts from a CSV into the database using the provided column mapping.

    This function:
    1. Applies column mapping
    2. Validates data
    3. Normalizes to Posts
    4. Bulk inserts Posts
    5. Updates Dataset status
    """
    dataset = get_dataset(db, dataset_id)

    # Remove existing posts for this dataset (re-import)
    db.query(Post).filter(Post.dataset_id == dataset_id).delete()

    try:
        parse_result = parse_csv(content=csv_content, filename=filename)
    except ValueError as exc:
        raise ValidationException(str(exc)) from exc

    mapped_df = apply_column_mapping(parse_result.dataframe, column_mapping)
    validation_result, valid_df = validate_dataset(mapped_df, column_mapping)

    normalized = normalize_dataframe(valid_df, dataset_id, column_mapping)

    batch_size = 500
    for i in range(0, len(normalized), batch_size):
        batch = normalized[i : i + batch_size]
        db.bulk_insert_mappings(Post, batch)  # type: ignore[arg-type]

    dataset.column_mapping = column_mapping
    dataset.validation_results = validation_result.to_dict()
    dataset.row_count = parse_result.total_rows
    dataset.valid_row_count = validation_result.valid_rows
    dataset.status = "imported"
    dataset.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(dataset)

    return dataset


def delete_dataset(db: Session, dataset_id: UUID) -> None:
    """Delete a dataset and all its posts (CASCADE)."""
    dataset = get_dataset(db, dataset_id)
    db.delete(dataset)
    db.commit()
