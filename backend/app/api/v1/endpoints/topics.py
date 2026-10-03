"""Thin topic list and investigation routes."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.schemas.topic import TopicDetailResponse, TopicListResponse
from app.services.topic_service import list_topics, topic_detail

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=TopicListResponse)
def get_topics(
    analysis_run_id: Optional[uuid.UUID] = None,
    dataset_id: Optional[uuid.UUID] = None,
    classification: Optional[str] = Query(None, pattern="^(emerging|rising|stable|declining)$"),
    q: Optional[str] = None,
    time_window: str = Query("daily", pattern="^(hourly|daily|weekly)$"),
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
) -> TopicListResponse:
    return list_topics(db, analysis_run_id, classification, q, time_window, platform, dataset_id)


@router.get("/{topic_id}", response_model=TopicDetailResponse)
def get_topic_detail(
    topic_id: uuid.UUID,
    analysis_run_id: Optional[uuid.UUID] = None,
    dataset_id: Optional[uuid.UUID] = None,
    time_window: str = Query("daily", pattern="^(hourly|daily|weekly)$"),
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
) -> TopicDetailResponse:
    return topic_detail(db, topic_id, analysis_run_id, dataset_id, time_window, platform)
