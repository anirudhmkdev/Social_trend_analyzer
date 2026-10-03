"""Pydantic schemas for dataset operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Column Mapping Schemas
# ---------------------------------------------------------------------------


class ColumnMappingRequest(BaseModel):
    """Column mapping submitted by the user."""

    text: Optional[str] = None
    timestamp: Optional[str] = None
    platform: Optional[str] = None
    hashtags: Optional[str] = None
    likes: Optional[str] = None
    comments: Optional[str] = None
    shares: Optional[str] = None
    author_id: Optional[str] = None
    external_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        return self.model_dump()


class ColumnDetectionResult(BaseModel):
    """Auto-detection result for a single field."""

    source_column: Optional[str] = None
    confidence: float = 0.0


class ColumnMappingResponse(BaseModel):
    """Response containing detected column mappings."""

    available_columns: List[str]
    detected: Dict[str, ColumnDetectionResult]
    ambiguous_fields: List[str]


# ---------------------------------------------------------------------------
# Validation Result Schemas
# ---------------------------------------------------------------------------


class ValidationIssueCount(BaseModel):
    missing_text: int = 0
    missing_timestamp: int = 0
    invalid_timestamp: int = 0
    duplicate_posts: int = 0


class DateRangeInfo(BaseModel):
    earliest: Optional[str] = None
    latest: Optional[str] = None


class ValidationResultSchema(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    issues: ValidationIssueCount
    date_range: DateRangeInfo
    platform_distribution: Dict[str, int]
    missing_field_counts: Dict[str, int]


# ---------------------------------------------------------------------------
# Dataset Schemas
# ---------------------------------------------------------------------------


class DatasetStatus:
    """Dataset status values."""

    UPLOADED = "uploaded"
    MAPPED = "mapped"
    VALIDATED = "validated"
    IMPORTING = "importing"
    IMPORTED = "imported"
    ERROR = "error"


class DatasetCreate(BaseModel):
    name: str
    source_type: str = "csv"


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    filename: str
    source_type: str
    file_size_bytes: Optional[int] = None
    row_count: Optional[int] = None
    valid_row_count: Optional[int] = None
    column_mapping: Optional[Dict[str, Any]] = None
    validation_results: Optional[Dict[str, Any]] = None
    preprocessing_version: str
    status: str
    created_at: datetime
    updated_at: datetime


class DatasetListResponse(BaseModel):
    datasets: List[DatasetResponse]
    total: int


class DatasetPreviewResponse(BaseModel):
    dataset_id: UUID
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: Optional[int] = None
    shown_rows: int


class SampleDatasetResponse(BaseModel):
    """Response when loading the sample dataset."""

    dataset_id: UUID
    name: str
    row_count: int
    message: str
