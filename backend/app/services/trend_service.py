"""Read-side trend views using the same scoring engine as analysis."""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationException
from app.models.analysis_run import AnalysisRun
from app.models.post import Post
from app.models.sentiment_result import SentimentResult
from app.models.topic import PostTopic, Topic
from app.nlp.trends.config import TrendConfig
from app.nlp.trends.engine import TrendEngine
from app.schemas.trend import TrendSnapshotResponse


def trend_histories(
    db: Session,
    run: AnalysisRun,
    time_window: str = "daily",
    platform: Optional[str] = None,
    topic_id: Optional[uuid.UUID] = None,
) -> Dict[uuid.UUID, List[TrendSnapshotResponse]]:
    """All results are run-scoped. Filtered/windowed views recompute, never relabel daily scores."""
    topics_stmt = select(Topic).where(Topic.analysis_run_id == run.id, Topic.is_outlier.is_(False))
    if topic_id:
        topics_stmt = topics_stmt.where(Topic.id == topic_id)
    topics = list(db.scalars(topics_stmt))
    all_posts = list(db.scalars(select(Post).where(Post.dataset_id == run.dataset_id)))
    if not all_posts:
        return {}
    reference = max(post.timestamp for post in all_posts)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    stmt = (
        select(PostTopic.topic_id, Post, SentimentResult.label)
        .join(Post, Post.id == PostTopic.post_id)
        .outerjoin(
            SentimentResult,
            (SentimentResult.post_id == Post.id) & (SentimentResult.analysis_run_id == run.id),
        )
        .where(PostTopic.analysis_run_id == run.id, Post.dataset_id == run.dataset_id)
        .order_by(Post.timestamp, Post.id)
    )
    if platform:
        stmt = stmt.where(Post.platform == platform.lower())
    if topic_id:
        stmt = stmt.where(PostTopic.topic_id == topic_id)
    grouped: Dict[uuid.UUID, list] = {}
    for tid, post, sentiment in db.execute(stmt):
        grouped.setdefault(tid, []).append(
            {
                "timestamp": post.timestamp,
                "likes": post.likes,
                "comments": post.comments,
                "shares": post.shares,
                "sentiment": sentiment,
            }
        )
    cfg = TrendConfig(time_window=time_window)
    engine = TrendEngine(cfg)
    result = {}
    for topic in topics:
        records = grouped.get(topic.id, [])
        if not records:
            continue
        has_engagement = any(
            record.get(field) is not None
            for record in records
            for field in ("likes", "comments", "shares")
        )
        try:
            snapshots = engine.analyze_topic(topic.id, records, reference, has_engagement)
        except ValueError as exc:
            raise ValidationException(
                "Date range is too large for this window. Choose daily or weekly."
            ) from exc
        history = []
        activity: List[int] = []
        for snap in snapshots:
            activity.append(snap.volume_current)
            history.append(
                TrendSnapshotResponse(
                    **snap.to_dict(),
                    id=uuid.uuid5(
                        run.id, f"{topic.id}/{time_window}/{platform}/{snap.window_start}"
                    ),
                    analysis_run_id=run.id,
                    topic_name=topic.display_name,
                    created_at=run.completed_at or datetime.now(timezone.utc),
                    activity=activity[-21:].copy(),
                    min_posts_for_trend=cfg.min_posts_for_trend,
                )
            )
        result[topic.id] = history
    return result


def ranked_trends(
    db: Session,
    run: AnalysisRun,
    time_window: str = "daily",
    platform: Optional[str] = None,
) -> List[TrendSnapshotResponse]:
    histories = trend_histories(db, run, time_window, platform)
    return sorted(
        [history[-1] for history in histories.values() if history],
        key=lambda trend: (-trend.trend_score, str(trend.topic_id)),
    )
