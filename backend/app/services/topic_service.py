"""Topic investigation with complete aggregates and explicitly sampled evidence."""

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import EntityNotFoundException, ValidationException
from app.models.entity import Entity, PostEntity
from app.models.post import Post
from app.models.sentiment_result import SentimentResult
from app.models.topic import PostTopic, Topic
from app.nlp.enrichment.keywords import KeywordExtractor
from app.schemas.topic import TopicDetailResponse, TopicListResponse, TopicResponse
from app.services.context import resolve_run
from app.services.dashboard_service import get_timeline
from app.services.trend_service import ranked_trends, trend_histories


def list_topics(
    db: Session,
    run_id: Optional[uuid.UUID],
    classification: Optional[str] = None,
    query: Optional[str] = None,
    time_window: str = "daily",
    platform: Optional[str] = None,
    dataset_id: Optional[uuid.UUID] = None,
) -> TopicListResponse:
    run = resolve_run(db, run_id, dataset_id)
    if run is None:
        return TopicListResponse(topics=[], total_topics=0, outlier_count=0)
    trends = {trend.topic_id: trend for trend in ranked_trends(db, run, time_window, platform)}
    topics = list(
        db.scalars(
            select(Topic)
            .where(Topic.analysis_run_id == run.id)
            .order_by(Topic.post_count.desc(), Topic.id)
        )
    )
    items = []
    for topic in topics:
        trend = trends.get(topic.id)
        if classification and (trend is None or trend.classification != classification):
            continue
        if platform and trend is None:
            continue
        if (
            query
            and query.casefold()
            not in (
                topic.display_name
                + " "
                + " ".join(str(keyword.get("word", "")) for keyword in topic.keywords)
            ).casefold()
        ):
            continue
        item = TopicResponse.model_validate(topic)
        item.latest_trend = trend
        items.append(item)
    return TopicListResponse(
        topics=items,
        total_topics=sum(not item.is_outlier for item in items),
        outlier_count=sum(topic.post_count for topic in topics if topic.is_outlier),
    )


def topic_detail(
    db: Session,
    topic_id: uuid.UUID,
    run_id: Optional[uuid.UUID] = None,
    dataset_id: Optional[uuid.UUID] = None,
    time_window: str = "daily",
    platform: Optional[str] = None,
) -> TopicDetailResponse:
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise EntityNotFoundException("Topic", str(topic_id))
    if run_id and topic.analysis_run_id != run_id:
        raise ValidationException("Topic does not belong to the selected analysis run.")
    run = resolve_run(db, topic.analysis_run_id, dataset_id)
    assert run is not None
    stmt = (
        select(PostTopic, Post, SentimentResult.label)
        .join(Post, Post.id == PostTopic.post_id)
        .outerjoin(
            SentimentResult,
            (SentimentResult.post_id == Post.id) & (SentimentResult.analysis_run_id == run.id),
        )
        .where(
            PostTopic.topic_id == topic.id,
            PostTopic.analysis_run_id == run.id,
            Post.dataset_id == run.dataset_id,
        )
        .order_by(PostTopic.probability.desc(), Post.timestamp.desc(), Post.id)
    )
    if platform:
        stmt = stmt.where(Post.platform == platform)
    rows = list(db.execute(stmt))
    posts = [post for _, post, _ in rows]
    counts = {
        label: sum(sentiment == label for _, _, sentiment in rows)
        for label in ("positive", "neutral", "negative")
    }
    total = sum(counts.values())
    distribution = {
        label: round(count * 100 / total, 2) if total else 0.0 for label, count in counts.items()
    }
    # NULL optional engagement remains unavailable; zeros are real measurements.
    engagement = {}
    for field in ("likes", "comments", "shares"):
        values = [getattr(post, field) for post in posts if getattr(post, field) is not None]
        engagement[field] = round(sum(values) / len(values), 2) if values else None
    post_ids = [post.id for post in posts]
    entities_stmt = (
        select(Entity.text, Entity.label, func.count(PostEntity.id))
        .join(
            PostEntity, (PostEntity.entity_id == Entity.id) & (PostEntity.analysis_run_id == run.id)
        )
        .where(Entity.analysis_run_id == run.id, PostEntity.post_id.in_(post_ids))
        .group_by(Entity.id, Entity.text, Entity.label)
        .order_by(func.count(PostEntity.id).desc())
        .limit(20)
    )
    entities = [
        {"text": text, "label": label, "frequency": count}
        for text, label, count in db.execute(entities_stmt)
    ]
    extractor = KeywordExtractor(max_features=100)
    histories = trend_histories(db, run, time_window, platform, topic_id=topic_id)
    item = TopicResponse.model_validate(topic)
    item.post_count = len(posts)
    history = histories.get(topic_id, [])
    item.latest_trend = history[-1] if history else None
    return TopicDetailResponse(
        topic=item,
        dataset_id=run.dataset_id,
        sentiment_distribution=distribution,
        avg_engagement=engagement,
        entities=entities,
        keywords=[
            kw.to_dict()
            for kw in extractor.extract_keywords(
                [post.cleaned_text or post.original_text for post in posts], top_n=15
            )
        ],
        hashtags=[
            ht.to_dict() for ht in extractor.analyze_hashtags([p.hashtags or [] for p in posts])
        ],
        trend_history=history,
        timeline=get_timeline(db, run.id, topic_id, time_window, run.dataset_id, platform).timeline,
        sample_posts=[
            {
                "id": str(post.id),
                "original_text": post.original_text,
                "timestamp": post.timestamp.isoformat(),
                "platform": post.platform,
                "sentiment": label,
                "likes": post.likes,
                "comments": post.comments,
                "shares": post.shares,
                "probability": assignment.probability,
            }
            for assignment, post, label in rows[:10]
        ],
    )
