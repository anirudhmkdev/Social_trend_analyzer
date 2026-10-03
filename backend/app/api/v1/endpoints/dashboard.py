"""API route handlers for dashboard analytics, timelines, posts search, and pipeline metadata."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    DashboardTimelineResponse,
    PipelineMetadataResponse,
    PostSearchResponse,
)
from app.services.dashboard_service import (
    get_dashboard_summary,
    get_pipeline_metadata,
    get_timeline,
    search_posts,
)

dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
posts_router = APIRouter(prefix="/posts", tags=["Posts"])
pipeline_router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


@dashboard_router.get("/summary", response_model=DashboardSummaryResponse)
def get_summary(
    analysis_run_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    """Retrieve unified summary metrics, top trends, entities, and keyword insights."""
    return get_dashboard_summary(db=db, run_id=analysis_run_id)


@dashboard_router.get("/timeline", response_model=DashboardTimelineResponse)
def get_timeline_data(
    analysis_run_id: Optional[uuid.UUID] = None,
    topic_id: Optional[uuid.UUID] = None,
    time_window: str = Query("daily", pattern="^(hourly|daily|weekly)$"),
    db: Session = Depends(get_db),
) -> DashboardTimelineResponse:
    """Retrieve temporal volume and sentiment breakdown across UTC calendar windows."""
    return get_timeline(
        db=db,
        run_id=analysis_run_id,
        topic_id=topic_id,
        time_window=time_window,
    )


@posts_router.get("/search", response_model=PostSearchResponse)
def search_posts_endpoint(
    dataset_id: Optional[uuid.UUID] = None,
    q: Optional[str] = Query(None, description="Search text in original or cleaned text"),
    sentiment: Optional[str] = Query(None, pattern="^(positive|neutral|negative)$"),
    platform: Optional[str] = Query(None, description="Social platform name"),
    topic_id: Optional[uuid.UUID] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> PostSearchResponse:
    """Search and filter posts with pagination, text search, and categorical facets."""
    return search_posts(
        db=db,
        dataset_id=dataset_id,
        query=q,
        sentiment=sentiment,
        platform=platform,
        topic_id=topic_id,
        limit=limit,
        offset=offset,
    )


@pipeline_router.get("/metadata", response_model=PipelineMetadataResponse)
def get_metadata(
    db: Session = Depends(get_db),
) -> PipelineMetadataResponse:
    """Retrieve system-level pipeline architecture, active models, licenses, and trend settings."""
    return get_pipeline_metadata(db=db)
