"""Dataset API endpoints: upload, sample, list, detail, preview, map-columns, validate, delete."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database.engine import get_db
from app.schemas.dataset import (
    ColumnMappingRequest,
    DatasetListResponse,
    DatasetPreviewResponse,
    DatasetResponse,
    SampleDatasetResponse,
    ValidationResultSchema,
)
from app.services import dataset_service

router = APIRouter(prefix="/datasets", tags=["datasets"])


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DatasetResponse:
    """
    Upload a CSV file and auto-detect column mappings.

    The file is parsed but NOT yet imported into the posts table.
    Use `/map-columns` to confirm mappings and `/import` to persist posts.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    content = await file.read(settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)

    dataset, parse_result = dataset_service.upload_csv(
        db=db,
        content=content,
        filename=file.filename,
    )

    return DatasetResponse.model_validate(dataset)


# ---------------------------------------------------------------------------
# Sample dataset
# ---------------------------------------------------------------------------


@router.post("/sample", response_model=SampleDatasetResponse, status_code=status.HTTP_201_CREATED)
def load_sample(db: Session = Depends(get_db)) -> SampleDatasetResponse:
    """
    Load the bundled synthetic demonstration dataset.

    The dataset is fully imported (posts are persisted).
    If the sample already exists it is returned without re-importing.
    """
    dataset = dataset_service.load_sample_dataset(db=db)
    total_posts = (
        db.query(dataset_service.Post).filter(dataset_service.Post.dataset_id == dataset.id).count()
    )
    return SampleDatasetResponse(
        dataset_id=dataset.id,
        name=dataset.name,
        row_count=total_posts,
        message=(
            "Sample dataset loaded successfully."
            if dataset.status == "imported"
            else "Sample dataset already exists."
        ),
    )


# ---------------------------------------------------------------------------
# List & Detail
# ---------------------------------------------------------------------------


@router.get("", response_model=DatasetListResponse)
def list_datasets(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> DatasetListResponse:
    """List all datasets with pagination."""
    datasets, total = dataset_service.list_datasets(db=db, limit=limit, offset=offset)
    return DatasetListResponse(
        datasets=[DatasetResponse.model_validate(d) for d in datasets],
        total=total,
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db),
) -> DatasetResponse:
    """Get dataset details by ID."""
    dataset = dataset_service.get_dataset(db=db, dataset_id=dataset_id)
    return DatasetResponse.model_validate(dataset)


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def preview_dataset(
    dataset_id: UUID,
    n_rows: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> DatasetPreviewResponse:
    """Preview staged raw rows before import, or normalized posts after import."""
    preview = dataset_service.get_dataset_preview(db=db, dataset_id=dataset_id, n_rows=n_rows)
    return DatasetPreviewResponse(**preview)


# ---------------------------------------------------------------------------
# Column mapping
# ---------------------------------------------------------------------------


@router.post("/{dataset_id}/map-columns", response_model=DatasetResponse)
def map_columns(
    dataset_id: UUID,
    mapping: ColumnMappingRequest,
    db: Session = Depends(get_db),
) -> DatasetResponse:
    """Submit column mappings for a dataset."""
    dataset = dataset_service.update_column_mapping(
        db=db,
        dataset_id=dataset_id,
        column_mapping=mapping.to_dict(),
    )
    return DatasetResponse.model_validate(dataset)


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------


@router.post("/{dataset_id}/validate", response_model=ValidationResultSchema)
def validate_dataset_endpoint(
    dataset_id: UUID,
    db: Session = Depends(get_db),
) -> ValidationResultSchema:
    """Validate the staged CSV under the confirmed mapping."""
    _, validation_dict = dataset_service.run_validation(db=db, dataset_id=dataset_id)
    return ValidationResultSchema(**validation_dict)


@router.post("/{dataset_id}/import", response_model=DatasetResponse)
def import_dataset(dataset_id: UUID, db: Session = Depends(get_db)) -> DatasetResponse:
    """Persist valid normalized rows from the previously uploaded CSV."""
    return DatasetResponse.model_validate(dataset_service.import_dataset(db, dataset_id))


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete a dataset and all its posts."""
    dataset_service.delete_dataset(db=db, dataset_id=dataset_id)
