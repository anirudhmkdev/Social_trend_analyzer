"""API routes for discovered topics."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import EntityNotFoundException
from app.database.engine import get_db
from app.models.analysis_run import AnalysisRun
from app.models.post import Post
from app.models.sentiment_result import SentimentResult
from app.models.topic import PostTopic, Topic
from app.schemas.topic import (
    TopicDetailResponse,
    TopicListResponse,
    TopicResponse,
)

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=TopicListResponse)
def get_topics(
    analysis_run_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
) -> TopicListResponse:
    """List topics for an analysis run. If run_id not provided, uses latest completed run."""
    if analysis_run_id is None:
        latest_run = (
            db.execute(
                select(AnalysisRun)
                .where(AnalysisRun.status == "completed")
                .order_by(AnalysisRun.completed_at.desc())
                .limit(1)
            )
            .scalar_one_or_none()
        )
        if not latest_run:
            return TopicListResponse(topics=[], total_topics=0, outlier_count=0)
        target_run_id = latest_run.id
    else:
        target_run_id = analysis_run_id

    stmt = (
        select(Topic)
        .where(Topic.analysis_run_id == target_run_id)
        .order_by(Topic.is_outlier.asc(), Topic.post_count.desc())
    )
    topics = list(db.execute(stmt).scalars().all())

    outliers = sum(1 for t in topics if t.is_outlier)
    non_outliers = len(topics) - outliers

    return TopicListResponse(
        topics=[TopicResponse.model_validate(t) for t in topics],
        total_topics=non_outliers,
        outlier_count=outliers,
    )


@router.get("/{topic_id}", response_model=TopicDetailResponse)
def get_topic_detail(
    topic_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> TopicDetailResponse:
    """Get topic details including sentiment distribution and sample posts."""
    topic = db.execute(select(Topic).where(Topic.id == topic_id)).scalar_one_or_none()
    if not topic:
        raise EntityNotFoundException("Topic", str(topic_id))

    # Retrieve associated posts and their sentiment
    post_topics_stmt = (
        select(PostTopic, Post)
        .join(Post, Post.id == PostTopic.post_id)
        .where(PostTopic.topic_id == topic.id)
        .limit(50)
    )
    results = db.execute(post_topics_stmt).all()

    sent_counts = {"positive": 0, "neutral": 0, "negative": 0}
    tot_likes = 0
    tot_comments = 0
    tot_shares = 0
    posts_sample = []

    post_ids = [p.id for _, p in results]
    sentiment_map = {}
    if post_ids:
        s_stmt = select(SentimentResult).where(
            SentimentResult.post_id.in_(post_ids),
            SentimentResult.analysis_run_id == topic.analysis_run_id,
        )
        for s in db.execute(s_stmt).scalars().all():
            sentiment_map[s.post_id] = s.label

    for pt, post in results:
        label = sentiment_map.get(post.id, "neutral")
        sent_counts[label] = sent_counts.get(label, 0) + 1
        tot_likes += post.likes or 0
        tot_comments += post.comments or 0
        tot_shares += post.shares or 0

        posts_sample.append({
            "id": str(post.id),
            "original_text": post.original_text,
            "timestamp": post.timestamp.isoformat(),
            "platform": post.platform,
            "sentiment": label,
            "likes": post.likes,
            "comments": post.comments,
            "shares": post.shares,
            "probability": pt.probability,
        })

    n = len(results) or 1
    sent_dist = {
        "positive": round(sent_counts["positive"] / n, 4),
        "neutral": round(sent_counts["neutral"] / n, 4),
        "negative": round(sent_counts["negative"] / n, 4),
    }
    avg_eng = {
        "likes": round(tot_likes / n, 2),
        "comments": round(tot_comments / n, 2),
        "shares": round(tot_shares / n, 2),
    }

    return TopicDetailResponse(
        topic=TopicResponse.model_validate(topic),
        sentiment_distribution=sent_dist,
        avg_engagement=avg_eng,
        sample_posts=posts_sample[:10],
    )
