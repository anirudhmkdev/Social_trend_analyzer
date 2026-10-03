import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalysisRunCreate(BaseModel):
    dataset_id: uuid.UUID = Field(..., description="Target dataset UUID")
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional pipeline parameter overrides"
    )


class AnalysisRunResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    status: str
    progress_pct: int
    current_step: Optional[str] = None
    config: Dict[str, Any]
    model_info: Optional[Dict[str, Any]] = None
    stats: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SentimentResultResponse(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    analysis_run_id: uuid.UUID
    label: str
    confidence: float
    score_positive: float
    score_neutral: float
    score_negative: float
    created_at: datetime

    model_config = {"from_attributes": True}


class SentimentSummaryResponse(BaseModel):
    analysis_run_id: uuid.UUID
    total_posts: int
    positive_count: int
    neutral_count: int
    negative_count: int
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    evaluation_metrics: Optional[Dict[str, Any]] = None


class AnalysisRunListResponse(BaseModel):
    runs: List[AnalysisRunResponse]
    total: int
