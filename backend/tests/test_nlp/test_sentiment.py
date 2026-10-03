"""Tests for Phase 4: Sentiment Analysis, Evaluation, and AnalysisRun Lifecycle."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException
from app.models.dataset import Dataset
from app.models.post import Post
from app.models.sentiment_result import SentimentResult
from app.nlp.sentiment.classifier import (
    SENTIMENT_LABELS,
    SENTIMENT_MODEL_LICENSE,
    SentimentAnalyzer,
    SentimentResultData,
)
from app.nlp.sentiment.evaluator import evaluate_sentiment_predictions
from app.services.analysis_service import (
    create_analysis_run,
    execute_analysis_run,
)


def test_sentiment_analyzer_metadata():
    analyzer = SentimentAnalyzer.get_instance()
    assert analyzer.license == SENTIMENT_MODEL_LICENSE
    assert analyzer.labels == SENTIMENT_LABELS
    assert set(analyzer.labels) == {"negative", "neutral", "positive"}


def test_sentiment_analyzer_prediction():
    analyzer = SentimentAnalyzer.get_instance()

    pos_text = "Incredible breakthrough in renewable energy! Solar efficiency hits record high."
    res_pos = analyzer.predict(pos_text)
    assert isinstance(res_pos, SentimentResultData)
    assert res_pos.label in SENTIMENT_LABELS
    assert 0.0 <= res_pos.confidence <= 1.0
    assert 0.0 <= res_pos.score_positive <= 1.0
    assert 0.0 <= res_pos.score_neutral <= 1.0
    assert 0.0 <= res_pos.score_negative <= 1.0

    neg_text = "Severe disaster and catastrophic loss reported in the affected region."
    res_neg = analyzer.predict(neg_text)
    assert res_neg.label in SENTIMENT_LABELS


def test_sentiment_analyzer_batch_prediction():
    analyzer = SentimentAnalyzer.get_instance()
    texts = [
        "Excited about AI progress! Great work!",
        "Economic outlook remains uncertain and risky.",
        "The conference will take place on Tuesday.",
    ]
    batch_res = analyzer.predict_batch(texts, batch_size=2)
    assert len(batch_res) == 3
    for r in batch_res:
        assert r.label in SENTIMENT_LABELS
        assert 0.0 <= r.confidence <= 1.0


def test_conditional_evaluation_with_ground_truth():
    y_true = ["positive", "negative", "neutral", "positive"]
    y_pred = ["positive", "negative", "positive", "positive"]

    metrics = evaluate_sentiment_predictions(y_true, y_pred)
    assert metrics is not None
    assert "accuracy" in metrics
    assert "macro_f1" in metrics
    assert "per_class" in metrics
    assert "confusion_matrix" in metrics
    assert metrics["sample_count"] == 4
    # 3 correct out of 4 -> 0.75
    assert metrics["accuracy"] == 0.75


def test_conditional_evaluation_without_ground_truth():
    # Empty ground truth
    assert evaluate_sentiment_predictions([], []) is None
    # None / empty strings only
    assert evaluate_sentiment_predictions(["", ""], ["positive", "neutral"]) is None


def test_analysis_run_concurrency_guard(db_session: Session):
    dataset = Dataset(
        name="Dataset For Concurrency",
        filename="test.csv",
        source_type="csv",
        status="ready",
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    # First run succeeds
    run1 = create_analysis_run(db_session, dataset.id)
    assert run1.status == "pending"

    # Second run while first is active raises ConflictException (HTTP 409)
    with pytest.raises(ConflictException):
        create_analysis_run(db_session, dataset.id)

    # Finish run1
    run1.status = "completed"
    db_session.commit()

    # Now another run can be created
    run2 = create_analysis_run(db_session, dataset.id)
    assert run2.status == "pending"


def test_analysis_pipeline_execution(db_session: Session):
    dataset = Dataset(
        name="Dataset For Pipeline Run",
        filename="test.csv",
        source_type="csv",
        status="uploaded",
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    posts = [
        Post(
            dataset_id=dataset.id,
            original_text="Wonderful AI achievements today! #AI",
            timestamp=datetime.now(timezone.utc),
        ),
        Post(
            dataset_id=dataset.id,
            original_text="Total disaster and failure of system. #crisis",
            timestamp=datetime.now(timezone.utc),
        ),
    ]
    db_session.add_all(posts)
    db_session.commit()

    run = create_analysis_run(db_session, dataset.id)

    # Execute pipeline
    execute_analysis_run(run.id, db_session=db_session)

    # Verify run completed
    db_session.refresh(run)
    assert run.status == "completed"
    assert run.progress_pct == 100
    assert run.started_at is not None
    assert run.completed_at is not None
    assert "sentiment" in run.stats
    assert run.stats["sentiment"]["total_posts"] == 2

    # Verify sentiment results in DB
    sent_results = (
        db_session.query(SentimentResult)
        .filter(SentimentResult.analysis_run_id == run.id)
        .all()
    )
    assert len(sent_results) == 2
    for s in sent_results:
        assert s.label in SENTIMENT_LABELS
        assert 0.0 <= s.confidence <= 1.0


def test_analysis_api_endpoints(client: TestClient, db_session: Session):

    dataset = Dataset(
        name="API Test Dataset",
        filename="api_test.csv",
        source_type="csv",
        status="uploaded",
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    # Trigger analysis run
    resp = client.post(
        "/api/v1/analysis/run",
        json={"dataset_id": str(dataset.id)},
    )
    assert resp.status_code == 201
    run_id = resp.json()["id"]

    # Active run endpoint
    resp_active = client.get("/api/v1/analysis/active")
    assert resp_active.status_code == 200

    # Status endpoint
    resp_status = client.get(f"/api/v1/analysis/{run_id}/status")
    assert resp_status.status_code == 200
    data = resp_status.json()
    assert data["id"] == run_id

    # Sentiment summary endpoint
    resp_sentiment = client.get(f"/api/v1/analysis/{run_id}/sentiment")
    assert resp_sentiment.status_code == 200
