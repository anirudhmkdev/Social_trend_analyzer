"""API routes for trend detection and snapshots."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.models.analysis_run import AnalysisRun
from app.models.topic import Topic
from app.models.trend_snapshot import TrendSnapshot
from app.schemas.trend import (
    TrendListResponse,
    TrendSnapshotResponse,
)

router = APIRouter(prefix="/trends", tags=["trends"])


def _resolve_run_id(db: Session, run_id: Optional[uuid.UUID]) -> Optional[uuid.UUID]:
    if run_id is not None:
        return run_id
    latest = db.execute(
        select(AnalysisRun)
        .where(AnalysisRun.status == "completed")
        .order_by(AnalysisRun.completed_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    return latest.id if latest else None


@router.get("", response_model=TrendListResponse)
def get_trends(
    analysis_run_id: Optional[uuid.UUID] = None,
    classification: Optional[str] = None,
    time_window: str = Query("daily", pattern="^(hourly|daily|weekly)$"),
    db: Session = Depends(get_db),
) -> TrendListResponse:
    """Retrieve latest trend snapshot per topic for the specified run."""
    run_id = _resolve_run_id(db, analysis_run_id)
    if not run_id:
        return TrendListResponse(
            trends=[],
            total=0,
            emerging_count=0,
            rising_count=0,
            stable_count=0,
            declining_count=0,
        )

    # Get distinct topics and their most recent snapshot
    subq = (
        select(TrendSnapshot)
        .join(Topic, Topic.id == TrendSnapshot.topic_id)
        .where(
            TrendSnapshot.analysis_run_id == run_id,
            TrendSnapshot.time_window == time_window,
            Topic.is_outlier.is_(False),  # Exclude outlier topics from ranked trend list
        )
    )
    if classification:
        subq = subq.where(TrendSnapshot.classification == classification.lower())

    subq = subq.order_by(desc(TrendSnapshot.window_start), desc(TrendSnapshot.trend_score))
    all_snaps = list(db.execute(subq).scalars().all())

    # Keep only the latest snapshot per topic
    seen_topics = set()
    latest_per_topic: List[TrendSnapshot] = []
    for s in all_snaps:
        if s.topic_id not in seen_topics:
            seen_topics.add(s.topic_id)
            latest_per_topic.append(s)

    # Sort by trend_score descending
    latest_per_topic.sort(key=lambda x: x.trend_score, reverse=True)

    # Attach topic names
    topic_ids = [s.topic_id for s in latest_per_topic]
    topics_map = {}
    if topic_ids:
        t_stmt = select(Topic).where(Topic.id.in_(topic_ids))
        for t in db.execute(t_stmt).scalars().all():
            topics_map[t.id] = t.display_name

    items: List[TrendSnapshotResponse] = []
    counts = {"emerging": 0, "rising": 0, "stable": 0, "declining": 0}

    for s in latest_per_topic:
        c = s.classification.lower()
        counts[c] = counts.get(c, 0) + 1
        resp = TrendSnapshotResponse.model_validate(s)
        resp.topic_name = topics_map.get(s.topic_id, "Unknown Topic")
        items.append(resp)

    return TrendListResponse(
        trends=items,
        total=len(items),
        emerging_count=counts["emerging"],
        rising_count=counts["rising"],
        stable_count=counts["stable"],
        declining_count=counts["declining"],
    )


@router.get("/topic/{topic_id}", response_model=List[TrendSnapshotResponse])
def get_topic_trend_history(
    topic_id: uuid.UUID,
    time_window: str = Query("daily", pattern="^(hourly|daily|weekly)$"),
    db: Session = Depends(get_db),
) -> List[TrendSnapshotResponse]:
    """Retrieve full chronological trajectory for a specific topic."""
    stmt = (
        select(TrendSnapshot)
        .where(
            TrendSnapshot.topic_id == topic_id,
            TrendSnapshot.time_window == time_window,
        )
        .order_by(TrendSnapshot.window_start.asc())
    )
    snaps = list(db.execute(stmt).scalars().all())

    topic = db.execute(select(Topic).where(Topic.id == topic_id)).scalar_one_or_none()
    topic_name = topic.display_name if topic else "Unknown Topic"

    res = []
    for s in snaps:
        r = TrendSnapshotResponse.model_validate(s)
        r.topic_name = topic_name
        res.append(r)
    return res
