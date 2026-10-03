import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class TopicResponse(BaseModel):
    id: uuid.UUID
    analysis_run_id: uuid.UUID
    topic_index: int
    display_name: str
    keywords: List[Dict[str, Any]]
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
    avg_engagement: Dict[str, float]  # likes, comments, shares
    sample_posts: List[Dict[str, Any]]
