"""Schemas for unified dashboard analytics, search, and pipeline metadata."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.trend import TrendSnapshotResponse


class TimelinePoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    window_start: datetime
    window_end: datetime
    total_volume: int
    positive_count: int
    neutral_count: int
    negative_count: int
    avg_engagement: float


class DashboardTimelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time_window: str
    timeline: List[TimelinePoint]
    total_points: int


class DashboardSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    analysis_run_id: Optional[uuid.UUID] = None
    dataset_id: Optional[uuid.UUID] = None
    dataset_name: Optional[str] = None
    status: str
    total_posts: int
    total_topics: int
    sentiment_breakdown: Dict[str, Any]
    trend_classifications: Dict[str, int]
    top_trends: List[TrendSnapshotResponse]
    top_entities: List[Dict[str, Any]]
    top_hashtags: List[Dict[str, Any]]
    top_keywords: List[Dict[str, Any]]
    platform_breakdown: Dict[str, int]
    model_info: Dict[str, Any]


class PostItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dataset_id: uuid.UUID
    original_text: str
    cleaned_text: Optional[str] = None
    sentiment_ready_text: Optional[str] = None
    timestamp: datetime
    platform: Optional[str] = None
    author_id: Optional[str] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    hashtags: Optional[List[str]] = None
    sentiment: Optional[str] = None
    topic_name: Optional[str] = None


class PostSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[PostItemResponse]
    total: int
    limit: int
    offset: int


class PipelineMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    preprocessing_version: str
    embedding_model: str
    embedding_dimensions: int
    sentiment_model: str
    sentiment_license: str
    ner_model: str
    topic_model: str
    trend_weights: Dict[str, float]
    trend_thresholds: Dict[str, float]
    active_run: Optional[Dict[str, Any]] = None
    database_backend: str
