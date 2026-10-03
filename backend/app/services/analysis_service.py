"""Service for orchestrating AnalysisRun lifecycle and pipeline execution."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, EntityNotFoundException
from app.database.engine import SessionLocal
from app.models.analysis_run import AnalysisRun
from app.models.dataset import Dataset
from app.models.post import Post
from app.models.sentiment_result import SentimentResult
from app.models.topic import PostTopic, Topic
from app.nlp.preprocessing.cleaner import PREPROCESSING_VERSION
from app.nlp.preprocessing.pipeline import run_dataset_preprocessing
from app.nlp.sentiment.classifier import (
    SENTIMENT_MODEL_LICENSE,
    SENTIMENT_MODEL_NAME,
    SentimentAnalyzer,
)
from app.nlp.sentiment.evaluator import evaluate_sentiment_predictions
from app.nlp.topics.embedder import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL_NAME,
    SentenceEmbedder,
)
from app.nlp.topics.modeler import TopicModeler

logger = logging.getLogger(__name__)


def get_active_analysis_run(db: Session) -> Optional[AnalysisRun]:
    """Return the currently pending or running AnalysisRun, if any."""
    stmt = (
        select(AnalysisRun)
        .where(AnalysisRun.status.in_(["pending", "running"]))
        .order_by(desc(AnalysisRun.created_at))
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def create_analysis_run(
    db: Session,
    dataset_id: uuid.UUID,
    config: Optional[Dict[str, Any]] = None,
) -> AnalysisRun:
    """Create and enqueue an analysis run. Strictly enforces 1 active run at a time."""
    # Check dataset existence
    dataset = db.execute(select(Dataset).where(Dataset.id == dataset_id)).scalar_one_or_none()
    if not dataset:
        raise EntityNotFoundException("Dataset", str(dataset_id))

    # Concurrency guard: Only 1 active analysis run allowed
    active_run = get_active_analysis_run(db)
    if active_run:
        raise ConflictException(
            f"An analysis run ({active_run.id}) is currently {active_run.status}. "
            "Only one active analysis run is permitted at a time."
        )

    pipeline_config = {
        "preprocessing_version": PREPROCESSING_VERSION,
        "sentiment_model": SENTIMENT_MODEL_NAME,
        "sentiment_license": SENTIMENT_MODEL_LICENSE,
        "batch_size": 32,
        "random_seed": 42,
        **(config or {}),
    }

    run = AnalysisRun(
        dataset_id=dataset_id,
        status="pending",
        progress_pct=0,
        current_step="Enqueued",
        config=pipeline_config,
        model_info={
            "sentiment_model": SENTIMENT_MODEL_NAME,
            "sentiment_license": SENTIMENT_MODEL_LICENSE,
        },
        stats={},
        created_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_analysis_run(db: Session, run_id: uuid.UUID) -> AnalysisRun:
    """Retrieve an AnalysisRun by ID."""
    run = db.execute(select(AnalysisRun).where(AnalysisRun.id == run_id)).scalar_one_or_none()
    if not run:
        raise EntityNotFoundException("AnalysisRun", str(run_id))
    return run


def list_analysis_runs(
    db: Session, dataset_id: Optional[uuid.UUID] = None
) -> List[AnalysisRun]:
    """List analysis runs optionally filtered by dataset."""
    stmt = select(AnalysisRun).order_by(desc(AnalysisRun.created_at))
    if dataset_id:
        stmt = stmt.where(AnalysisRun.dataset_id == dataset_id)
    return list(db.execute(stmt).scalars().all())


def execute_analysis_run(
    run_id: uuid.UUID, db_session: Optional[Session] = None
) -> None:
    """Synchronous pipeline worker function to run as background task or in tests."""
    should_close = False
    if db_session is not None:
        db = db_session
    else:
        db = SessionLocal()
        should_close = True
    try:
        run = db.execute(select(AnalysisRun).where(AnalysisRun.id == run_id)).scalar_one_or_none()
        if not run:
            logger.error("AnalysisRun %s not found for execution", run_id)
            return

        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        run.current_step = "Preprocessing"
        run.progress_pct = 10
        db.commit()

        # Step 1: Preprocessing
        logger.info("Executing preprocessing for dataset %s...", run.dataset_id)
        preproc_summary = run_dataset_preprocessing(db, run.dataset_id)
        run.progress_pct = 25
        run.current_step = "Sentiment Analysis"
        db.commit()

        # Step 2: Sentiment Analysis
        posts = db.execute(
            select(Post)
            .where(Post.dataset_id == run.dataset_id)
            .order_by(Post.timestamp.asc())
        ).scalars().all()

        if not posts:
            run.status = "completed"
            run.progress_pct = 100
            run.completed_at = datetime.now(timezone.utc)
            run.current_step = "Completed (empty dataset)"
            db.commit()
            return

        logger.info("Running sentiment inference on %d posts...", len(posts))
        texts = [p.sentiment_ready_text or p.original_text for p in posts]
        analyzer = SentimentAnalyzer.get_instance()
        predictions = analyzer.predict_batch(texts, batch_size=32)

        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        y_pred: List[str] = []
        y_true: List[str] = []

        sentiment_objects = []
        for post, pred in zip(posts, predictions):
            sentiment_counts[pred.label] += 1
            y_pred.append(pred.label)

            # Check if ground-truth sentiment exists in post preprocessing metadata or source
            gt = None
            if post.preprocessing_meta and "ground_truth_sentiment" in post.preprocessing_meta:
                gt = str(post.preprocessing_meta["ground_truth_sentiment"]).lower()
            y_true.append(gt or "")

            sent_res = SentimentResult(
                post_id=post.id,
                analysis_run_id=run.id,
                label=pred.label,
                confidence=pred.confidence,
                score_positive=pred.score_positive,
                score_neutral=pred.score_neutral,
                score_negative=pred.score_negative,
                created_at=datetime.now(timezone.utc),
            )
            sentiment_objects.append(sent_res)

        db.add_all(sentiment_objects)
        db.commit()

        run.progress_pct = 40
        db.commit()

        # Conditional Evaluation (ONLY if ground truth labels exist)
        eval_metrics = evaluate_sentiment_predictions(y_true, y_pred)

        total_posts = len(posts)
        sentiment_stats = {
            "total_posts": total_posts,
            "positive_count": sentiment_counts["positive"],
            "neutral_count": sentiment_counts["neutral"],
            "negative_count": sentiment_counts["negative"],
            "positive_pct": round(sentiment_counts["positive"] / total_posts, 4),
            "neutral_pct": round(sentiment_counts["neutral"] / total_posts, 4),
            "negative_pct": round(sentiment_counts["negative"] / total_posts, 4),
            "evaluation_metrics": eval_metrics,
        }

        # Step 3: Embeddings & Topic Modeling
        run.progress_pct = 50
        run.current_step = "Sentence Embeddings & Topic Modeling"
        db.commit()

        cleaned_texts = [p.cleaned_text or p.original_text for p in posts]
        embedder = SentenceEmbedder.get_instance()
        embeddings = embedder.encode(cleaned_texts, batch_size=64)

        topic_modeler = TopicModeler(random_state=42)
        topic_labels, probs, discovered_topics = topic_modeler.fit_transform(
            cleaned_texts, embeddings=embeddings
        )

        topic_id_map: Dict[int, uuid.UUID] = {}
        topic_objects = []
        for dt in discovered_topics:
            topic_rec = Topic(
                analysis_run_id=run.id,
                topic_index=dt.topic_index,
                display_name=dt.display_name,
                keywords=dt.keywords,
                representative_docs=dt.representative_docs,
                post_count=len(dt.post_indices),
                is_outlier=dt.is_outlier,
                created_at=datetime.now(timezone.utc),
            )
            topic_objects.append(topic_rec)

        db.add_all(topic_objects)
        db.commit()

        # Map topic_index to newly assigned Topic.id
        for t in topic_objects:
            topic_id_map[t.topic_index] = t.id

        post_topic_objects = []
        for i, post in enumerate(posts):
            t_idx = topic_labels[i]
            if t_idx in topic_id_map:
                pt = PostTopic(
                    post_id=post.id,
                    topic_id=topic_id_map[t_idx],
                    analysis_run_id=run.id,
                    probability=probs[i] if i < len(probs) else 1.0,
                )
                post_topic_objects.append(pt)

        db.add_all(post_topic_objects)
        db.commit()

        topics_stats = {
            "total_topics": len([t for t in discovered_topics if not t.is_outlier]),
            "outlier_count": len([i for i in topic_labels if i == -1]),
            "discovered_count": len(discovered_topics),
        }

        run.model_info = {
            **(run.model_info or {}),
            "embedding_model": EMBEDDING_MODEL_NAME,
            "embedding_dimensions": EMBEDDING_DIMENSIONS,
            "topic_model": "BERTopic + UMAP + HDBSCAN + c-TF-IDF",
        }

        run.stats = {
            **(run.stats or {}),
            "preprocessing": preproc_summary,
            "sentiment": sentiment_stats,
            "topics": topics_stats,
        }
        run.progress_pct = 100
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        run.current_step = "Completed"
        db.commit()
        logger.info("AnalysisRun %s completed successfully.", run_id)

    except Exception as exc:
        logger.exception("Error executing AnalysisRun %s: %s", run_id, exc)
        try:
            stmt = select(AnalysisRun).where(AnalysisRun.id == run_id)
            run = db.execute(stmt).scalar_one_or_none()
            if run:
                run.status = "failed"
                run.error_message = str(exc)
                run.completed_at = datetime.now(timezone.utc)
                run.current_step = "Failed"
                db.commit()
        except Exception:
            pass
    finally:
        if should_close:
            db.close()
