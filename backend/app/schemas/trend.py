import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TrendSnapshotResponse(BaseModel):
    id: uuid.UUID
    analysis_run_id: uuid.UUID
    topic_id: uuid.UUID
    topic_name: Optional[str] = None
    time_window: str
    window_start: datetime
    window_end: datetime
    trend_score: float
    classification: str
    explanation: str
    volume_current: int
    volume_previous: int
    volume_growth_pct: Optional[float] = None
    engagement_current: Optional[float] = None
    engagement_previous: Optional[float] = None
    engagement_growth_pct: Optional[float] = None
    velocity: Optional[float] = None
    burst_score: Optional[float] = None
    recency_score: Optional[float] = None
    sentiment_positive_pct: Optional[float] = None
    sentiment_neutral_pct: Optional[float] = None
    sentiment_negative_pct: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TrendListResponse(BaseModel):
    trends: List[TrendSnapshotResponse]
    total: int
    emerging_count: int
    rising_count: int
    stable_count: int
    declining_count: int
