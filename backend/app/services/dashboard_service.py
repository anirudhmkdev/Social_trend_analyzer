"""Service orchestrating dashboard analytics, aggregations, timelines, and search."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import EntityNotFoundException, ValidationException
from app.models.analysis_run import AnalysisRun
from app.models.dataset import Dataset
from app.models.entity import Entity, PostEntity
from app.models.post import Post
from app.models.sentiment_result import SentimentResult
from app.models.topic import PostTopic, Topic
from app.nlp.enrichment.keywords import KeywordExtractor
from app.nlp.enrichment.ner import NER_MODEL_NAME, EntityRecognizer
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
from app.services.analysis_service import get_active_analysis_run
from app.services.context import resolve_run
from app.services.trend_service import ranked_trends


def _resolve_completed_run(db: Session, run_id: Optional[uuid.UUID]) -> Optional[AnalysisRun]:
    return resolve_run(db, run_id)


def get_dashboard_summary(
    db: Session,
    run_id: Optional[uuid.UUID] = None,
    dataset_id: Optional[uuid.UUID] = None,
    time_window: str = "daily",
    platform: Optional[str] = None,
) -> DashboardSummaryResponse:
    """Generate unified overview summary metrics for the analytics dashboard."""
    run = resolve_run(db, run_id, dataset_id)
    if not run:
        return DashboardSummaryResponse(
            status="no_data",
            total_posts=0,
            total_topics=0,
            sentiment_breakdown={
                "counts": {"positive": 0, "neutral": 0, "negative": 0},
                "percentages": {"positive": 0, "neutral": 0, "negative": 0},
                "total": 0,
            },
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
    post_stmt = select(Post).where(Post.dataset_id == run.dataset_id)
    if platform:
        post_stmt = post_stmt.where(Post.platform == platform.lower())
    posts = list(db.scalars(post_stmt))
    post_ids = [post.id for post in posts]
    total_posts = len(posts)

    platform_breakdown: Dict[str, int] = {}
    for p in posts:
        plat = (p.platform or "other").lower()
        platform_breakdown[plat] = platform_breakdown.get(plat, 0) + 1

    # Sentiment distribution
    sent_counts = {"positive": 0, "neutral": 0, "negative": 0}
    sent_stmt = (
        select(SentimentResult.label, func.count(SentimentResult.id))
        .where(SentimentResult.analysis_run_id == run.id, SentimentResult.post_id.in_(post_ids))
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

    top_trend_responses = ranked_trends(db, run, time_window, platform)
    total_topics = len(top_trend_responses)
    trend_classifications = {"emerging": 0, "rising": 0, "stable": 0, "declining": 0}
    for trend in top_trend_responses:
        trend_classifications[trend.classification] += 1

    ent_stmt = (
        select(Entity.text, Entity.label, func.count(PostEntity.id))
        .join(
            PostEntity, (PostEntity.entity_id == Entity.id) & (PostEntity.analysis_run_id == run.id)
        )
        .where(Entity.analysis_run_id == run.id, PostEntity.post_id.in_(post_ids))
        .group_by(Entity.id, Entity.text, Entity.label)
        .order_by(func.count(PostEntity.id).desc(), Entity.text)
        .limit(10)
    )
    top_entities = [
        {"text": text, "label": label, "frequency": frequency}
        for text, label, frequency in db.execute(ent_stmt)
    ]
    extractor = KeywordExtractor(max_features=100)
    texts = [post.cleaned_text or post.original_text for post in posts]
    top_keywords = [keyword.to_dict() for keyword in extractor.extract_keywords(texts, top_n=10)]
    top_hashtags = [
        hashtag.to_dict()
        for hashtag in extractor.analyze_hashtags([post.hashtags or [] for post in posts])[:10]
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
        top_trends=top_trend_responses[:10],
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
    dataset_id: Optional[uuid.UUID] = None,
    platform: Optional[str] = None,
) -> DashboardTimelineResponse:
    """Retrieve temporal volume and sentiment breakdown per window."""
    run = resolve_run(db, run_id, dataset_id)
    if not run:
        return DashboardTimelineResponse(time_window=time_window, timeline=[], total_points=0)

    if topic_id:
        topic = db.get(Topic, topic_id)
        if topic is None:
            raise EntityNotFoundException("Topic", str(topic_id))
        if topic.analysis_run_id != run.id:
            raise ValidationException("Topic does not belong to the selected analysis run.")
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

    if platform:
        post_stmt = post_stmt.where(Post.platform == platform.lower())
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
    reference = db.scalar(select(func.max(Post.timestamp)).where(Post.dataset_id == run.dataset_id))
    try:
        grouped = aggregator.group_posts_by_window(posts_data, reference)
    except ValueError as exc:
        raise ValidationException(
            "Date range is too large for this window. Choose daily or weekly."
        ) from exc

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
    run_id: Optional[uuid.UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> PostSearchResponse:
    run = resolve_run(db, run_id, dataset_id)
    if dataset_id is None:
        if run is None:
            raise ValidationException("Choose a dataset to search posts.")
        dataset_id = run.dataset_id
    if (sentiment or topic_id) and run is None:
        raise ValidationException("Choose a completed analysis run for sentiment/topic filters.")
    if topic_id:
        topic = db.get(Topic, topic_id)
        if topic is None:
            raise EntityNotFoundException("Topic", str(topic_id))
        if run is None or topic.analysis_run_id != run.id:
            raise ValidationException("Topic does not belong to the selected analysis run.")

    def utc(value: datetime) -> datetime:
        return (
            value.replace(tzinfo=timezone.utc)
            if value.tzinfo is None
            else value.astimezone(timezone.utc)
        )

    if date_from:
        date_from = utc(date_from)
    if date_to:
        date_to = utc(date_to)
    if date_from and date_to and date_from > date_to:
        raise ValidationException("Start date must not be later than end date.")
    target_run = run.id if run else None
    stmt = (
        select(Post, SentimentResult.label, Topic.display_name)
        .outerjoin(
            SentimentResult,
            (SentimentResult.post_id == Post.id) & (SentimentResult.analysis_run_id == target_run),
        )
        .outerjoin(
            PostTopic, (PostTopic.post_id == Post.id) & (PostTopic.analysis_run_id == target_run)
        )
        .outerjoin(Topic, (Topic.id == PostTopic.topic_id) & (Topic.analysis_run_id == target_run))
        .where(Post.dataset_id == dataset_id)
    )
    if platform:
        stmt = stmt.where(Post.platform == platform.lower())
    if sentiment:
        stmt = stmt.where(SentimentResult.label == sentiment.lower())
    if topic_id:
        stmt = stmt.where(PostTopic.topic_id == topic_id)
    if date_from:
        stmt = stmt.where(Post.timestamp >= date_from)
    if date_to:
        stmt = stmt.where(Post.timestamp <= date_to)
    if query and query.strip():
        literal = (
            query.strip().lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        stmt = stmt.where(
            func.lower(Post.original_text).like(f"%{literal}%", escape="\\")
            | func.lower(Post.cleaned_text).like(f"%{literal}%", escape="\\")
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.order_by(Post.timestamp.desc(), Post.id).offset(offset).limit(limit))
    items = []
    for post, label, name in rows:
        item = PostItemResponse.model_validate(post)
        item.sentiment = label
        item.topic_name = name
        items.append(item)
    return PostSearchResponse(items=items, total=total, limit=limit, offset=offset)


def get_pipeline_metadata(
    db: Session, run_id: Optional[uuid.UUID] = None
) -> PipelineMetadataResponse:
    """Return pipeline metadata, model architectures, trend parameters, and system status."""
    run = resolve_run(db, run_id, require_completed=False)
    packages = {}
    for package in (
        "transformers",
        "torch",
        "sentence-transformers",
        "spacy",
        "bertopic",
        "umap-learn",
        "hdbscan",
    ):
        try:
            packages[package] = version(package)
        except PackageNotFoundError:
            packages[package] = "not installed"
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
        package_versions=packages,
        run_model_info=(run.model_info or {}) if run else {},
        run_stats=(run.stats or {}) if run else {},
        ner_status=EntityRecognizer.get_instance().metadata(),
        min_posts_for_trend=trend_cfg.min_posts_for_trend,
    )
