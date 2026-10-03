"""Service orchestrating dashboard analytics, aggregations, timelines, and search."""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.analysis_run import AnalysisRun
from app.models.dataset import Dataset
from app.models.entity import Entity
from app.models.keyword_snapshot import KeywordSnapshot
from app.models.post import Post
from app.models.sentiment_result import SentimentResult
from app.models.topic import PostTopic, Topic
from app.models.trend_snapshot import TrendSnapshot
from app.nlp.enrichment.ner import NER_MODEL_NAME
from app.nlp.preprocessing.cleaner import PREPROCESSING_VERSION
from app.nlp.sentiment.classifier import (
    SENTIMENT_MODEL_LICENSE,
    SENTIMENT_MODEL_NAME,
)
from app.nlp.topics.embedder import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL_NAME,
)
from app.nlp.trends.aggregator import (
    TemporalAggregator,
    get_utc_window_end,
)
from app.nlp.trends.config import TrendConfig
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    DashboardTimelineResponse,
    PipelineMetadataResponse,
    PostItemResponse,
    PostSearchResponse,
    TimelinePoint,
)
from app.schemas.trend import TrendSnapshotResponse
from app.services.analysis_service import get_active_analysis_run


def _resolve_completed_run(db: Session, run_id: Optional[uuid.UUID]) -> Optional[AnalysisRun]:
    """Retrieve run by ID or default to the most recent completed run."""
    if run_id:
        return db.execute(select(AnalysisRun).where(AnalysisRun.id == run_id)).scalar_one_or_none()
    return db.execute(
        select(AnalysisRun)
        .where(AnalysisRun.status == "completed")
        .order_by(desc(AnalysisRun.completed_at))
        .limit(1)
    ).scalar_one_or_none()


def get_dashboard_summary(
    db: Session, run_id: Optional[uuid.UUID] = None
) -> DashboardSummaryResponse:
    """Generate unified overview summary metrics for the analytics dashboard."""
    run = _resolve_completed_run(db, run_id)
    if not run:
        return DashboardSummaryResponse(
            status="no_data",
            total_posts=0,
            total_topics=0,
            sentiment_breakdown={"positive": 0, "neutral": 0, "negative": 0, "pct": {}},
            trend_classifications={"emerging": 0, "rising": 0, "stable": 0, "declining": 0},
            top_trends=[],
            top_entities=[],
            top_hashtags=[],
            top_keywords=[],
            platform_breakdown={},
            model_info={},
        )

    dataset = db.execute(select(Dataset).where(Dataset.id == run.dataset_id)).scalar_one_or_none()
    dataset_name = dataset.name if dataset else "Unknown Dataset"

    # Total posts & platform breakdown
    posts = list(db.execute(select(Post).where(Post.dataset_id == run.dataset_id)).scalars().all())
    total_posts = len(posts)

    platform_breakdown: Dict[str, int] = {}
    for p in posts:
        plat = (p.platform or "other").lower()
        platform_breakdown[plat] = platform_breakdown.get(plat, 0) + 1

    # Sentiment distribution
    sent_counts = {"positive": 0, "neutral": 0, "negative": 0}
    sent_stmt = (
        select(SentimentResult.label, func.count(SentimentResult.id))
        .where(SentimentResult.analysis_run_id == run.id)
        .group_by(SentimentResult.label)
    )
    for label, count in db.execute(sent_stmt).all():
        if label in sent_counts:
            sent_counts[label] = count

    sent_total = sum(sent_counts.values())
    sent_pct = {
        k: round((v / sent_total) * 100, 1) if sent_total > 0 else 0.0
        for k, v in sent_counts.items()
    }

    # Topics & Trends
    topics = list(
        db.execute(
            select(Topic).where(Topic.analysis_run_id == run.id, Topic.is_outlier.is_(False))
        )
        .scalars()
        .all()
    )
    topics_map = {t.id: t.display_name for t in topics}
    total_topics = len(topics)

    # Latest trend snapshot per topic
    trend_snaps_stmt = (
        select(TrendSnapshot)
        .join(Topic, Topic.id == TrendSnapshot.topic_id)
        .where(
            TrendSnapshot.analysis_run_id == run.id,
            TrendSnapshot.time_window == "daily",
            Topic.is_outlier.is_(False),
        )
        .order_by(desc(TrendSnapshot.window_start), desc(TrendSnapshot.trend_score))
    )
    all_trend_snaps = list(db.execute(trend_snaps_stmt).scalars().all())

    seen_topics = set()
    latest_trends: List[TrendSnapshot] = []
    for s in all_trend_snaps:
        if s.topic_id not in seen_topics:
            seen_topics.add(s.topic_id)
            latest_trends.append(s)

    latest_trends.sort(key=lambda x: x.trend_score, reverse=True)

    trend_classifications = {"emerging": 0, "rising": 0, "stable": 0, "declining": 0}
    top_trend_responses: List[TrendSnapshotResponse] = []
    for s in latest_trends:
        c = s.classification.lower()
        if c in trend_classifications:
            trend_classifications[c] += 1
        resp = TrendSnapshotResponse.model_validate(s)
        resp.topic_name = topics_map.get(s.topic_id, "Unknown Topic")
        top_trend_responses.append(resp)

    # Top Entities
    ent_stmt = (
        select(Entity)
        .where(Entity.analysis_run_id == run.id)
        .order_by(desc(Entity.frequency))
        .limit(5)
    )
    top_entities = [
        {"text": e.text, "label": e.label, "frequency": e.frequency}
        for e in db.execute(ent_stmt).scalars().all()
    ]

    # Top Hashtags & Keywords
    kw_stmt = select(KeywordSnapshot).where(KeywordSnapshot.analysis_run_id == run.id)
    all_kws = list(db.execute(kw_stmt).scalars().all())

    hashtags = [k for k in all_kws if k.keyword_type == "hashtag"]
    hashtags.sort(key=lambda x: x.frequency, reverse=True)
    top_hashtags = [
        {"keyword": h.keyword, "frequency": h.frequency, "growth_rate": h.growth_rate}
        for h in hashtags[:10]
    ]

    keywords = [k for k in all_kws if k.keyword_type != "hashtag"]
    keywords.sort(key=lambda x: x.tfidf_score or 0.0, reverse=True)
    top_keywords = [
        {
            "keyword": k.keyword,
            "frequency": k.frequency,
            "tfidf_score": round(k.tfidf_score, 4) if k.tfidf_score else 0.0,
        }
        for k in keywords[:10]
    ]

    return DashboardSummaryResponse(
        analysis_run_id=run.id,
        dataset_id=run.dataset_id,
        dataset_name=dataset_name,
        status=run.status,
        total_posts=total_posts,
        total_topics=total_topics,
        sentiment_breakdown={
            "counts": sent_counts,
            "percentages": sent_pct,
            "total": sent_total,
        },
        trend_classifications=trend_classifications,
        top_trends=top_trend_responses[:5],
        top_entities=top_entities,
        top_hashtags=top_hashtags,
        top_keywords=top_keywords,
        platform_breakdown=platform_breakdown,
        model_info=run.model_info or {},
    )


def get_timeline(
    db: Session,
    run_id: Optional[uuid.UUID] = None,
    topic_id: Optional[uuid.UUID] = None,
    time_window: str = "daily",
) -> DashboardTimelineResponse:
    """Retrieve temporal volume and sentiment breakdown per window."""
    run = _resolve_completed_run(db, run_id)
    if not run:
        return DashboardTimelineResponse(time_window=time_window, timeline=[], total_points=0)

    # Fetch posts for run
    if topic_id:
        post_stmt = (
            select(Post, SentimentResult.label)
            .join(PostTopic, PostTopic.post_id == Post.id)
            .outerjoin(
                SentimentResult,
                (SentimentResult.post_id == Post.id) & (SentimentResult.analysis_run_id == run.id),
            )
            .where(
                Post.dataset_id == run.dataset_id,
                PostTopic.topic_id == topic_id,
                PostTopic.analysis_run_id == run.id,
            )
            .order_by(Post.timestamp.asc())
        )
    else:
        post_stmt = (
            select(Post, SentimentResult.label)
            .outerjoin(
                SentimentResult,
                (SentimentResult.post_id == Post.id) & (SentimentResult.analysis_run_id == run.id),
            )
            .where(Post.dataset_id == run.dataset_id)
            .order_by(Post.timestamp.asc())
        )

    results = db.execute(post_stmt).all()
    posts_data = []
    for p, sent_label in results:
        posts_data.append(
            {
                "timestamp": p.timestamp,
                "likes": p.likes,
                "comments": p.comments,
                "shares": p.shares,
                "sentiment": sent_label or "neutral",
            }
        )

    aggregator = TemporalAggregator(time_window=time_window)
    grouped = aggregator.group_posts_by_window(posts_data)

    points: List[TimelinePoint] = []
    for w_start, p_list in grouped.items():
        w_end = get_utc_window_end(w_start, time_window)
        vol = len(p_list)
        pos = sum(1 for x in p_list if x.get("sentiment") == "positive")
        neu = sum(1 for x in p_list if x.get("sentiment") == "neutral")
        neg = sum(1 for x in p_list if x.get("sentiment") == "negative")

        tot_eng = sum(
            (x.get("likes") or 0) + (x.get("comments") or 0) + (x.get("shares") or 0)
            for x in p_list
        )
        avg_eng = round(tot_eng / float(vol), 2) if vol > 0 else 0.0

        points.append(
            TimelinePoint(
                window_start=w_start,
                window_end=w_end,
                total_volume=vol,
                positive_count=pos,
                neutral_count=neu,
                negative_count=neg,
                avg_engagement=avg_eng,
            )
        )

    return DashboardTimelineResponse(
        time_window=time_window,
        timeline=points,
        total_points=len(points),
    )


def search_posts(
    db: Session,
    dataset_id: Optional[uuid.UUID] = None,
    query: Optional[str] = None,
    sentiment: Optional[str] = None,
    platform: Optional[str] = None,
    topic_id: Optional[uuid.UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> PostSearchResponse:
    """Filter and search posts with text search and categorical facets."""
    stmt = (
        select(Post, SentimentResult.label, Topic.display_name)
        .outerjoin(SentimentResult, SentimentResult.post_id == Post.id)
        .outerjoin(PostTopic, PostTopic.post_id == Post.id)
        .outerjoin(Topic, Topic.id == PostTopic.topic_id)
    )

    if dataset_id:
        stmt = stmt.where(Post.dataset_id == dataset_id)

    if platform:
        stmt = stmt.where(Post.platform == platform.lower())

    if sentiment:
        stmt = stmt.where(SentimentResult.label == sentiment.lower())

    if topic_id:
        stmt = stmt.where(PostTopic.topic_id == topic_id)

    if query and query.strip():
        q_term = f"%{query.strip().lower()}%"
        stmt = stmt.where(
            func.lower(Post.original_text).like(q_term) | func.lower(Post.cleaned_text).like(q_term)
        )

    # Total count query
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = db.execute(count_stmt).scalar() or 0

    # Paginate and order by timestamp descending
    stmt = stmt.order_by(desc(Post.timestamp)).offset(offset).limit(limit)
    rows = db.execute(stmt).all()

    items: List[PostItemResponse] = []
    for post, sent, t_name in rows:
        item = PostItemResponse(
            id=post.id,
            dataset_id=post.dataset_id,
            original_text=post.original_text,
            cleaned_text=post.cleaned_text,
            sentiment_ready_text=post.sentiment_ready_text,
            timestamp=post.timestamp,
            platform=post.platform,
            author_id=post.author_id,
            likes=post.likes,
            comments=post.comments,
            shares=post.shares,
            hashtags=post.hashtags,
            sentiment=sent,
            topic_name=t_name,
        )
        items.append(item)

    return PostSearchResponse(
        items=items,
        total=total_count,
        limit=limit,
        offset=offset,
    )


def get_pipeline_metadata(db: Session) -> PipelineMetadataResponse:
    """Return pipeline metadata, model architectures, trend parameters, and system status."""
    trend_cfg = TrendConfig()
    active_run = get_active_analysis_run(db)

    active_dict = None
    if active_run:
        active_dict = {
            "id": str(active_run.id),
            "dataset_id": str(active_run.dataset_id),
            "status": active_run.status,
            "current_step": active_run.current_step,
            "progress_pct": active_run.progress_pct,
            "started_at": active_run.started_at.isoformat() if active_run.started_at else None,
        }

    db_backend = "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql"

    return PipelineMetadataResponse(
        preprocessing_version=PREPROCESSING_VERSION,
        embedding_model=EMBEDDING_MODEL_NAME,
        embedding_dimensions=EMBEDDING_DIMENSIONS,
        sentiment_model=SENTIMENT_MODEL_NAME,
        sentiment_license=SENTIMENT_MODEL_LICENSE,
        ner_model=NER_MODEL_NAME,
        topic_model="BERTopic + UMAP + HDBSCAN + c-TF-IDF",
        trend_weights={
            "volume": trend_cfg.weight_volume,
            "engagement": trend_cfg.weight_engagement,
            "velocity": trend_cfg.weight_velocity,
            "burstiness": trend_cfg.weight_burstiness,
        },
        trend_thresholds={
            "emerging": trend_cfg.threshold_emerging,
            "rising": trend_cfg.threshold_rising,
            "stable": trend_cfg.threshold_stable,
        },
        active_run=active_dict,
        database_backend=db_backend,
    )
