"""Service for orchestrating AnalysisRun lifecycle and pipeline execution."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, EntityNotFoundException, ValidationException
from app.database.engine import SessionLocal
from app.models.analysis_run import AnalysisRun
from app.models.dataset import Dataset
from app.models.entity import Entity, PostEntity
from app.models.keyword_snapshot import KeywordSnapshot
from app.models.post import Post
from app.models.sentiment_result import SentimentResult
from app.models.topic import PostTopic, Topic
from app.models.trend_snapshot import TrendSnapshot
from app.nlp.enrichment.keywords import KeywordExtractor
from app.nlp.enrichment.ner import NER_MODEL_NAME, EntityRecognizer
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
from app.nlp.trends.config import TrendConfig
from app.nlp.trends.engine import TrendEngine

logger = logging.getLogger(__name__)
_enqueue_lock = Lock()


def package_versions() -> Dict[str, str]:
    result = {}
    for name in [
        "transformers",
        "sentence-transformers",
        "torch",
        "spacy",
        "bertopic",
        "umap-learn",
        "hdbscan",
        "scikit-learn",
        "numpy",
        "pandas",
    ]:
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            result[name] = "not installed"
    return result


def get_active_analysis_run(db: Session) -> Optional[AnalysisRun]:
    """Return the currently pending or running AnalysisRun, if any."""
    stmt = (
        select(AnalysisRun)
        .where(AnalysisRun.status.in_(["pending", "running"]))
        .order_by(desc(AnalysisRun.created_at))
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def recover_interrupted_runs(db: Session) -> None:
    """The documented single-process server cannot resume in-memory jobs after restart."""
    for run in db.scalars(
        select(AnalysisRun).where(AnalysisRun.status.in_(["pending", "running"]))
    ):
        run.status = "failed"
        run.current_step = "Interrupted"
        run.error_message = "Analysis was interrupted by a server restart. Run analysis again."
        run.completed_at = datetime.now(timezone.utc)
    db.commit()


def _create_analysis_run(
    db: Session,
    dataset_id: uuid.UUID,
    config: Optional[Dict[str, Any]] = None,
) -> AnalysisRun:
    """Create and enqueue an analysis run. Strictly enforces 1 active run at a time."""
    # Check dataset existence
    dataset = db.execute(select(Dataset).where(Dataset.id == dataset_id)).scalar_one_or_none()
    if not dataset:
        raise EntityNotFoundException("Dataset", str(dataset_id))
    if dataset.status not in {"imported", "preprocessed"}:
        raise ConflictException("Import and validate this dataset before analysis.")
    if not db.scalar(select(Post.id).where(Post.dataset_id == dataset.id).limit(1)):
        raise ValidationException(
            "Dataset contains no imported posts. Upload valid data before analysis."
        )
    if config:
        raise ValidationException(
            "This pipeline uses fixed, versioned settings; parameter overrides are unsupported."
        )

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


def create_analysis_run(
    db: Session,
    dataset_id: uuid.UUID,
    config: Optional[Dict[str, Any]] = None,
) -> AnalysisRun:
    """Serialize check-and-enqueue for the documented single-process local server."""
    with _enqueue_lock:
        return _create_analysis_run(db, dataset_id, config)


def get_analysis_run(db: Session, run_id: uuid.UUID) -> AnalysisRun:
    """Retrieve an AnalysisRun by ID."""
    run = db.execute(select(AnalysisRun).where(AnalysisRun.id == run_id)).scalar_one_or_none()
    if not run:
        raise EntityNotFoundException("AnalysisRun", str(run_id))
    return run


def list_analysis_runs(db: Session, dataset_id: Optional[uuid.UUID] = None) -> List[AnalysisRun]:
    """List analysis runs optionally filtered by dataset."""
    stmt = select(AnalysisRun).order_by(desc(AnalysisRun.created_at))
    if dataset_id:
        if db.get(Dataset, dataset_id) is None:
            raise EntityNotFoundException("Dataset", str(dataset_id))
        stmt = stmt.where(AnalysisRun.dataset_id == dataset_id)
    return list(db.execute(stmt).scalars().all())


def execute_analysis_run(run_id: uuid.UUID, db_session: Optional[Session] = None) -> None:
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
        posts = (
            db.execute(
                select(Post).where(Post.dataset_id == run.dataset_id).order_by(Post.timestamp.asc())
            )
            .scalars()
            .all()
        )

        if not posts:
            raise ValidationException("Dataset contains no imported posts.")

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
                model_metadata=dt.model_metadata,
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

        # Step 4: NLP Enrichment (NER, Keywords, Hashtags)
        run.progress_pct = 70
        run.current_step = "NLP Enrichment (NER, Keywords, Hashtags)"
        db.commit()

        # 4a. NER Extraction
        raw_texts = [p.original_text for p in posts]
        ner = EntityRecognizer.get_instance()
        extracted_by_post = ner.extract_from_texts(raw_texts, batch_size=64)

        # Aggregate unique entities: key = (normalized_text, label)
        from collections import defaultdict

        entity_freqs: Dict[Tuple[str, str], int] = defaultdict(int)
        entity_display: Dict[Tuple[str, str], str] = {}
        for doc_ents in extracted_by_post:
            for ent in doc_ents:
                key = (ent.normalized_text, ent.label)
                entity_freqs[key] += 1
                if key not in entity_display:
                    entity_display[key] = ent.text

        entity_id_map: Dict[Tuple[str, str], uuid.UUID] = {}
        entity_objects = []
        for (norm_text, label), freq in entity_freqs.items():
            ent_rec = Entity(
                analysis_run_id=run.id,
                text=entity_display[(norm_text, label)],
                normalized_text=norm_text,
                label=label,
                frequency=freq,
            )
            entity_objects.append(ent_rec)

        db.add_all(entity_objects)
        db.commit()

        for ent_rec in entity_objects:
            entity_id_map[(ent_rec.normalized_text, ent_rec.label)] = ent_rec.id

        # Create PostEntity links
        post_entity_objects = []
        for post, doc_ents in zip(posts, extracted_by_post):
            for ent in doc_ents:
                key = (ent.normalized_text, ent.label)
                if key in entity_id_map:
                    pe = PostEntity(
                        post_id=post.id,
                        entity_id=entity_id_map[key],
                        analysis_run_id=run.id,
                        start_char=ent.start_char,
                        end_char=ent.end_char,
                    )
                    post_entity_objects.append(pe)

        db.add_all(post_entity_objects)
        db.commit()

        # 4b. Keywords & Hashtags
        kw_extractor = KeywordExtractor(max_features=100)
        top_keywords = kw_extractor.extract_keywords(cleaned_texts, top_n=50)
        hashtag_items = kw_extractor.analyze_hashtags(
            [p.hashtags or [] for p in posts],
            period_split_index=len(posts) // 2 if len(posts) > 4 else None,
        )

        keyword_objects = []
        for kw in top_keywords:
            k_rec = KeywordSnapshot(
                analysis_run_id=run.id,
                keyword=kw.keyword,
                keyword_type=kw.keyword_type,
                frequency=kw.frequency,
                tfidf_score=kw.tfidf_score,
                growth_rate=kw.growth_rate,
                created_at=datetime.now(timezone.utc),
            )
            keyword_objects.append(k_rec)

        for ht in hashtag_items:
            h_rec = KeywordSnapshot(
                analysis_run_id=run.id,
                keyword=ht.keyword,
                keyword_type="hashtag",
                frequency=ht.frequency,
                growth_rate=ht.growth_rate,
                created_at=datetime.now(timezone.utc),
            )
            keyword_objects.append(h_rec)

        db.add_all(keyword_objects)
        db.commit()

        enrichment_stats = {
            "total_entities": len(entity_objects),
            "total_keywords": len(top_keywords),
            "total_hashtags": len(hashtag_items),
        }

        # Step 5: Trend Detection Engine
        run.progress_pct = 85
        run.current_step = "Trend Detection"
        db.commit()

        has_engagement = any(
            p.likes is not None or p.shares is not None or p.comments is not None for p in posts
        )

        trend_config = TrendConfig()
        trend_engine = TrendEngine(config=trend_config)
        dataset_max_time = max(
            (p.timestamp for p in posts if p.timestamp is not None),
            default=datetime.now(timezone.utc),
        )
        if dataset_max_time.tzinfo is None:
            dataset_max_time = dataset_max_time.replace(tzinfo=timezone.utc)

        post_sentiment_map = {post.id: pred.label for post, pred in zip(posts, predictions)}
        trend_snapshot_objects: List[TrendSnapshot] = []

        for topic_rec in topic_objects:
            if topic_rec.is_outlier:
                continue

            topic_post_indices = [
                i for i, label in enumerate(topic_labels) if label == topic_rec.topic_index
            ]
            topic_posts_data = []
            for idx in topic_post_indices:
                p = posts[idx]
                topic_posts_data.append(
                    {
                        "timestamp": p.timestamp,
                        "likes": p.likes,
                        "comments": p.comments,
                        "shares": p.shares,
                        "sentiment": post_sentiment_map.get(p.id, "neutral"),
                    }
                )

            computed_snapshots = trend_engine.analyze_topic(
                topic_id=topic_rec.id,
                posts_data=topic_posts_data,
                now_utc=dataset_max_time,
                has_engagement=has_engagement,
            )

            for cs in computed_snapshots:
                ts_rec = TrendSnapshot(
                    analysis_run_id=run.id,
                    topic_id=cs.topic_id,
                    time_window=cs.time_window,
                    window_start=cs.window_start,
                    window_end=cs.window_end,
                    trend_score=cs.trend_score,
                    classification=cs.classification,
                    explanation=cs.explanation,
                    volume_current=cs.volume_current,
                    volume_previous=cs.volume_previous,
                    volume_growth_pct=cs.volume_growth_pct,
                    engagement_current=cs.engagement_current,
                    engagement_previous=cs.engagement_previous,
                    engagement_growth_pct=cs.engagement_growth_pct,
                    velocity=cs.velocity,
                    burst_score=cs.burst_score,
                    recency_score=cs.recency_score,
                    sentiment_positive_pct=cs.sentiment_positive_pct,
                    sentiment_neutral_pct=cs.sentiment_neutral_pct,
                    sentiment_negative_pct=cs.sentiment_negative_pct,
                    created_at=datetime.now(timezone.utc),
                )
                trend_snapshot_objects.append(ts_rec)

        db.add_all(trend_snapshot_objects)
        db.commit()

        trend_classification_counts = {
            "emerging": sum(1 for s in trend_snapshot_objects if s.classification == "emerging"),
            "rising": sum(1 for s in trend_snapshot_objects if s.classification == "rising"),
            "stable": sum(1 for s in trend_snapshot_objects if s.classification == "stable"),
            "declining": sum(1 for s in trend_snapshot_objects if s.classification == "declining"),
        }

        trends_stats = {
            "total_snapshots": len(trend_snapshot_objects),
            "topics_evaluated": len([t for t in topic_objects if not t.is_outlier]),
            "classifications": trend_classification_counts,
        }

        run.model_info = {
            **(run.model_info or {}),
            "package_versions": package_versions(),
            "sentiment": analyzer.metadata(),
            "embeddings": embedder.metadata(),
            "embedding_model": EMBEDDING_MODEL_NAME,
            "embedding_dimensions": EMBEDDING_DIMENSIONS,
            "topic_model": topic_modeler.metadata.get("method"),
            "topic_parameters": topic_modeler.metadata,
            "ner_model": NER_MODEL_NAME,
            "ner": ner.metadata(),
            "degraded": ner.status != "available",
            "warnings": [ner.error] if ner.error else [],
            "reference_time": dataset_max_time.isoformat(),
            "trend_weights": {
                "volume": trend_config.weight_volume,
                "engagement": trend_config.weight_engagement,
                "velocity": trend_config.weight_velocity,
                "burstiness": trend_config.weight_burstiness,
            },
        }

        run.stats = {
            **(run.stats or {}),
            "preprocessing": preproc_summary,
            "sentiment": sentiment_stats,
            "topics": topics_stats,
            "enrichment": enrichment_stats,
            "trends": trends_stats,
        }
        run.progress_pct = 100
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        run.current_step = "Completed"
        db.commit()
        logger.info("AnalysisRun %s completed successfully with trends.", run_id)

    except Exception as exc:
        logger.exception("Error executing AnalysisRun %s: %s", run_id, exc)
        try:
            db.rollback()
            stmt = select(AnalysisRun).where(AnalysisRun.id == run_id)
            run = db.execute(stmt).scalar_one_or_none()
            if run:
                run.status = "failed"
                run.error_message = str(exc)
                run.completed_at = datetime.now(timezone.utc)
                run.current_step = "Failed"
                db.commit()
        except Exception:
            logger.exception("Could not persist the failed status for analysis %s", run_id)
    finally:
        if should_close:
            db.close()
