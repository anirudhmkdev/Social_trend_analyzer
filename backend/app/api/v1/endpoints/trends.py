"""Latest-window classification filtering; never retrieve historical matches as current."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.schemas.trend import TrendListResponse, TrendSnapshotResponse
from app.services.context import resolve_run
from app.services.topic_service import topic_detail
from app.services.trend_service import ranked_trends, trend_histories

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("", response_model=TrendListResponse)
def get_trends(
    analysis_run_id: Optional[uuid.UUID] = None,
    dataset_id: Optional[uuid.UUID] = None,
    classification: Optional[str] = Query(None, pattern="^(emerging|rising|stable|declining)$"),
    time_window: str = Query("daily", pattern="^(hourly|daily|weekly)$"),
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
) -> TrendListResponse:
    run = resolve_run(db, analysis_run_id, dataset_id)
    trends = ranked_trends(db, run, time_window, platform) if run else []
    counts = {
        label: sum(trend.classification == label for trend in trends)
        for label in ("emerging", "rising", "stable", "declining")
    }
    if classification:
        trends = [trend for trend in trends if trend.classification == classification]
    return TrendListResponse(
        trends=trends,
        total=len(trends),
        **{f"{label}_count": count for label, count in counts.items()},
    )


@router.get("/topic/{topic_id}", response_model=List[TrendSnapshotResponse])
def get_topic_trend_history(
    topic_id: uuid.UUID,
    analysis_run_id: Optional[uuid.UUID] = None,
    dataset_id: Optional[uuid.UUID] = None,
    platform: Optional[str] = None,
    time_window: str = Query("daily", pattern="^(hourly|daily|weekly)$"),
    db: Session = Depends(get_db),
) -> List[TrendSnapshotResponse]:
    detail = topic_detail(db, topic_id, analysis_run_id, dataset_id, time_window, platform)
    run = resolve_run(db, detail.topic.analysis_run_id)
    assert run is not None
    return trend_histories(db, run, time_window, topic_id=topic_id).get(topic_id, [])
