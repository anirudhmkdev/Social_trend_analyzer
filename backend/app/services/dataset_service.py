"""Dataset service: orchestrates CSV ingestion, column mapping, validation and normalization."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import ConflictException, EntityNotFoundException, ValidationException
from app.core.logging import logger
from app.ingestion.csv_parser import (
    ParseResult,
    apply_column_mapping,
    get_csv_preview,
    parse_csv,
)
from app.ingestion.normalizer import normalize_dataframe
from app.ingestion.sample_generator import generate_sample_dataset
from app.ingestion.validator import validate_dataset
from app.models.analysis_run import AnalysisRun
from app.models.dataset import Dataset
from app.models.post import Post

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _staged_path(dataset: Dataset) -> Path:
    """Only server-generated UUID filenames can be resolved in the upload directory."""
    expected = f"{dataset.id.hex}.csv"
    if dataset.staged_filename != expected:
        raise ValidationException(
            "The staged CSV is unavailable. Delete this upload and upload again."
        )
    return Path(settings.UPLOAD_DIR).resolve() / expected


def _read_staged(dataset: Dataset) -> ParseResult:
    try:
        content = _staged_path(dataset).read_bytes()
        return parse_csv(content, dataset.filename, settings.MAX_UPLOAD_SIZE_MB)
    except (OSError, ValueError) as exc:
        raise ValidationException(
            "Cannot read the staged CSV. Delete this upload and upload again."
        ) from exc


def _check_mapping(mapping: Dict[str, Optional[str]], columns: List[str]) -> None:
    for required in ("text", "timestamp"):
        if not mapping.get(required):
            raise ValidationException(f"Choose a {required} column before validation.")
    selected = [v for v in mapping.values() if v is not None]
    if any(v not in columns for v in selected):
        raise ValidationException("Mapping references a column that is not in the uploaded CSV.")
    if len(selected) != len(set(selected)):
        raise ValidationException("Map each CSV column to only one field.")


def _assert_mutable(dataset: Dataset) -> None:
    if dataset.status in {"imported", "preprocessed"}:
        raise ConflictException(
            "Imported datasets are immutable. Upload a new dataset to change mappings."
        )


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

    # Build initial column_mapping dict from auto-detection
    detected_mapping = {
        field: source_col for field, source_col in parse_result.column_mapping.mappings.items()
    }

    dataset_id = uuid.uuid4()
    safe_filename = filename.replace("\\", "/").split("/")[-1][:500]
    dataset = Dataset(
        id=dataset_id,
        name=os.path.splitext(safe_filename)[0][:255],
        filename=safe_filename,
        staged_filename=f"{dataset_id.hex}.csv",
        upload_metadata={
            "encoding": parse_result.encoding_used,
            "warnings": parse_result.warnings,
            "ambiguous_fields": parse_result.column_mapping.ambiguous_fields,
        },
        source_type="csv",
        file_size_bytes=len(content),
        row_count=parse_result.total_rows,
        column_mapping=detected_mapping,
        status="uploaded",
    )
    path = _staged_path(dataset)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
    except Exception as exc:
        db.rollback()
        path.unlink(missing_ok=True)
        if isinstance(exc, OSError):
            raise ValidationException(
                "Cannot stage the upload. Check upload directory permissions."
            ) from exc
        raise

    return dataset, parse_result


def load_sample_dataset(db: Session) -> Dataset:
    """
    Load the bundled synthetic demo dataset into the database.

    Creates a Dataset record and imports all Posts.

    Returns the created Dataset.
    """
    # Check if sample already exists
    existing = db.query(Dataset).filter(Dataset.source_type == "synthetic_demo").first()
    if existing is not None:
        if existing.row_count != 900:
            raise ConflictException(
                "This stored demo uses an older generator. Delete it from Datasets, then use "
                "Demo Dataset again to load the current 900-post version."
            )
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
        db.query(Dataset).order_by(Dataset.created_at.desc()).limit(limit).offset(offset).all()
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
    dataset = get_dataset(db, dataset_id)
    if dataset.status not in {"imported", "preprocessed"}:
        parsed = _read_staged(dataset)
        detection = parsed.column_mapping
        return {
            "dataset_id": dataset_id,
            "columns": detection.available_columns,
            "rows": get_csv_preview(parsed.dataframe, n_rows),
            "total_rows": parsed.total_rows,
            "shown_rows": min(parsed.total_rows, n_rows),
            "kind": "raw",
            "warnings": parsed.warnings,
            "detection": {
                "available_columns": detection.available_columns,
                "ambiguous_fields": detection.ambiguous_fields,
                "detected": {
                    field: {"source_column": col, "confidence": detection.confidence[field]}
                    for field, col in detection.mappings.items()
                },
            },
        }
    posts = (
        db.query(Post)
        .filter(Post.dataset_id == dataset_id)
        .order_by(Post.timestamp)
        .limit(n_rows)
        .all()
    )
    total_posts = db.query(Post).filter(Post.dataset_id == dataset_id).count()

    columns = [
        "id",
        "original_text",
        "timestamp",
        "platform",
        "hashtags",
        "likes",
        "comments",
        "shares",
        "is_duplicate",
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
    _assert_mutable(dataset)
    parsed = _read_staged(dataset)
    _check_mapping(column_mapping, parsed.column_mapping.available_columns)
    dataset.column_mapping = column_mapping
    dataset.validation_results = None
    dataset.valid_row_count = None
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

    if dataset.status in {"imported", "preprocessed"} and dataset.validation_results:
        return dataset, dataset.validation_results
    if dataset.status not in {"mapped", "validated"}:
        raise ConflictException("Confirm the column mapping before validation.")
    parsed = _read_staged(dataset)
    mapping = dataset.column_mapping or {}
    _check_mapping(mapping, parsed.column_mapping.available_columns)
    result, _ = validate_dataset(apply_column_mapping(parsed.dataframe, mapping), mapping)
    result_dict = result.to_dict()

    dataset.validation_results = result_dict
    dataset.row_count = result.total_rows
    dataset.valid_row_count = result.valid_rows
    dataset.status = "validated"
    dataset.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(dataset)

    return dataset, result_dict


def import_dataset(
    db: Session,
    dataset_id: UUID,
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

    if dataset.status in {"imported", "preprocessed"}:
        return dataset
    if dataset.status != "validated":
        raise ConflictException("Validate the dataset before importing.")
    parse_result = _read_staged(dataset)
    column_mapping = dataset.column_mapping or {}
    _check_mapping(column_mapping, parse_result.column_mapping.available_columns)
    mapped_df = apply_column_mapping(parse_result.dataframe, column_mapping)
    validation_result, valid_df = validate_dataset(mapped_df, column_mapping)

    normalized = normalize_dataframe(valid_df, dataset_id, column_mapping)
    if not normalized:
        raise ValidationException(
            "No valid rows to import. Correct the mapping or upload a corrected CSV."
        )
    if len(normalized) != validation_result.valid_rows:
        raise ValidationException("Normalization disagrees with validation; no rows were imported.")

    batch_size = 500
    try:
        dataset.status = "importing"  # transaction-local; failure rolls back to validated
        for i in range(0, len(normalized), batch_size):
            db.bulk_insert_mappings(Post, normalized[i : i + batch_size])  # type: ignore[arg-type]
        dataset.validation_results = validation_result.to_dict()
        dataset.row_count = parse_result.total_rows
        dataset.valid_row_count = validation_result.valid_rows
        dataset.status = "imported"
        dataset.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(dataset)
    except Exception:
        db.rollback()
        raise

    return dataset


def delete_dataset(db: Session, dataset_id: UUID) -> None:
    """Delete a dataset and all its posts (CASCADE)."""
    dataset = get_dataset(db, dataset_id)
    if (
        db.query(AnalysisRun)
        .filter(
            AnalysisRun.dataset_id == dataset_id, AnalysisRun.status.in_(["pending", "running"])
        )
        .first()
    ):
        raise ConflictException(
            "Wait for the active analysis to finish before deleting this dataset."
        )
    path = _staged_path(dataset) if dataset.staged_filename else None
    # Fail before deleting records if the tracked artifact cannot be removed.
    if path:
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise ConflictException(
                "Cannot remove the staged CSV. Check directory permissions and retry."
            ) from exc
    db.delete(dataset)
    db.commit()
