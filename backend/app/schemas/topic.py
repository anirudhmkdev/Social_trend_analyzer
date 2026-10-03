import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.schemas.dashboard import TimelinePoint
from app.schemas.trend import TrendSnapshotResponse


class TopicResponse(BaseModel):
    id: uuid.UUID
    analysis_run_id: uuid.UUID
    topic_index: int
    display_name: str
    keywords: List[Dict[str, Any]]
    model_metadata: Optional[Dict[str, Any]] = None
    latest_trend: Optional[TrendSnapshotResponse] = None
    representative_docs: Optional[List[str]] = None
    post_count: int
    is_outlier: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TopicListResponse(BaseModel):
    topics: List[TopicResponse]
    total_topics: int
    outlier_count: int


class TopicDetailResponse(BaseModel):
    topic: TopicResponse
    sentiment_distribution: Dict[str, float]  # positive, neutral, negative %
    avg_engagement: Dict[str, Optional[float]]  # NULL is unavailable; zero is measured
    sample_posts: List[Dict[str, Any]]
    dataset_id: uuid.UUID
    entities: List[Dict[str, Any]] = []
    keywords: List[Dict[str, Any]] = []
    hashtags: List[Dict[str, Any]] = []
    trend_history: List[TrendSnapshotResponse] = []
    timeline: List[TimelinePoint] = []
