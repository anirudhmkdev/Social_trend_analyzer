"""Lifecycle, isolation and failure regressions uncovered by the takeover audit."""

import io
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import func, select

from app.config import settings
from app.ingestion.sample_generator import generate_sample_dataset
from app.models.analysis_run import AnalysisRun
from app.models.dataset import Dataset
from app.models.post import Post
from app.models.sentiment_result import SentimentResult
from app.models.topic import PostTopic, Topic
from app.nlp.enrichment.ner import EntityRecognizer
from app.nlp.sentiment.classifier import SentimentAnalyzer
from app.nlp.topics.embedder import SentenceEmbedder
from app.services.analysis_service import create_analysis_run, execute_analysis_run

CSV = (
    "body,when,network,likes,id\n"
    "OpenAI launched a model,2026-09-01T10:00:00Z,twitter,0,0001\n"
    "OpenAI launched a model,2026-09-02T10:00:00Z,reddit,10,0002\n"
    "New research findings,2026-09-03T10:00:00Z,youtube,5,0003\n"
    ",2026-09-03T10:00:00Z,twitter,,0004\n"
    "Invalid timestamp example,nonsense,twitter,3,0005\n"
)


def stage(client, csv=CSV):
    result = client.post(
        "/api/v1/datasets/upload", files={"file": ("../fixture.csv", csv.encode(), "text/csv")}
    )
    assert result.status_code == 201, result.text
    return result.json()["id"]


def test_upload_once_lifecycle_and_cascade(client, db_session):
    dataset_id = stage(client)
    dataset = db_session.get(Dataset, uuid.UUID(dataset_id))
    staged = Path(settings.UPLOAD_DIR) / dataset.staged_filename
    assert staged.exists() and staged.parent == Path(settings.UPLOAD_DIR)
    assert dataset.filename == "fixture.csv"
    preview = client.get(f"/api/v1/datasets/{dataset_id}/preview").json()
    assert preview["kind"] == "raw" and preview["rows"][0]["id"] == "0001"
    assert client.post(f"/api/v1/datasets/{dataset_id}/import").status_code == 409
    mapping = {
        "text": "body",
        "timestamp": "when",
        "platform": "network",
        "likes": "likes",
        "external_id": "id",
    }
    assert (
        client.post(f"/api/v1/datasets/{dataset_id}/map-columns", json=mapping).status_code == 200
    )
    result = client.post(f"/api/v1/datasets/{dataset_id}/validate").json()
    assert (result["total_rows"], result["valid_rows"], result["invalid_rows"]) == (5, 3, 2)
    assert result["issues"]["duplicate_posts"] == 1 and len(result["row_issues"]) == 3
    assert client.post(f"/api/v1/datasets/{dataset_id}/import").json()["status"] == "imported"
    assert client.post(f"/api/v1/datasets/{dataset_id}/import").status_code == 200
    posts = db_session.scalars(select(Post).where(Post.dataset_id == dataset.id)).all()
    assert len(posts) == 3 and any(post.likes == 0 for post in posts)
    assert (
        client.post(f"/api/v1/datasets/{dataset_id}/map-columns", json=mapping).status_code == 409
    )
    run = create_analysis_run(db_session, dataset.id)
    assert client.delete(f"/api/v1/datasets/{dataset_id}").status_code == 409
    execute_analysis_run(run.id, db_session)
    assert run.status == "completed"
    assert client.delete(f"/api/v1/datasets/{dataset_id}").status_code == 204
    assert not staged.exists()
    for model in [Post, AnalysisRun, Topic, PostTopic, SentimentResult]:
        assert db_session.scalar(select(func.count()).select_from(model)) == 0


def test_mapping_and_zero_valid_recovery(client):
    dataset_id = stage(client, "body,when\nhello,not-a-date\n")
    base = f"/api/v1/datasets/{dataset_id}"
    assert (
        client.post(
            base + "/map-columns", json={"text": "body", "timestamp": "missing"}
        ).status_code
        == 422
    )
    assert (
        client.post(base + "/map-columns", json={"text": "body", "timestamp": "body"}).status_code
        == 422
    )
    assert (
        client.post(base + "/map-columns", json={"text": "body", "timestamp": "when"}).status_code
        == 200
    )
    assert client.post(base + "/validate").json()["valid_rows"] == 0
    assert client.post(base + "/import").status_code == 422
    assert client.post("/api/v1/analysis/run", json={"dataset_id": dataset_id}).status_code == 409


def test_two_runs_never_duplicate_or_mix_search_and_topic_evidence(client, db_session):
    dataset = Dataset(
        name="Isolation", filename="fixture.csv", source_type="csv", status="imported"
    )
    db_session.add(dataset)
    db_session.flush()
    post = Post(
        dataset_id=dataset.id,
        original_text="Literal 100% AI_",
        timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc),
        platform="twitter",
    )
    db_session.add(post)
    db_session.flush()
    runs = []
    for label in ["positive", "negative"]:
        run = AnalysisRun(dataset_id=dataset.id, status="completed", config={}, stats={})
        db_session.add(run)
        db_session.flush()
        topic = Topic(
            analysis_run_id=run.id,
            topic_index=0,
            display_name=label,
            keywords=[],
            post_count=1,
            is_outlier=False,
        )
        db_session.add(topic)
        db_session.flush()
        db_session.add(
            PostTopic(analysis_run_id=run.id, topic_id=topic.id, post_id=post.id, probability=0.8)
        )
        db_session.add(
            SentimentResult(
                analysis_run_id=run.id,
                post_id=post.id,
                label=label,
                confidence=0.8,
                score_positive=0.8 if label == "positive" else 0.1,
                score_neutral=0.1,
                score_negative=0.8 if label == "negative" else 0.1,
            )
        )
        runs.append((run, topic))
    db_session.commit()
    for run, topic in runs:
        context = {"dataset_id": str(dataset.id), "analysis_run_id": str(run.id)}
        result = client.get(
            "/api/v1/posts/search", params={**context, "q": "100%", "limit": 1}
        ).json()
        assert result["total"] == 1 and len(result["items"]) == 1
        assert result["items"][0]["sentiment"] == topic.display_name
        summary = client.get("/api/v1/dashboard/summary", params=context).json()
        assert summary["sentiment_breakdown"]["counts"][topic.display_name] == 1
        assert summary["top_trends"][0]["volume_current"] == 1
        assert "insufficient current volume" in summary["top_trends"][0]["explanation"]
        assert (
            client.get(
                "/api/v1/topics/" + str(topic.id),
                params={
                    "analysis_run_id": str(runs[1][0].id if run == runs[0][0] else runs[0][0].id)
                },
            ).status_code
            == 422
        )
    assert client.get("/api/v1/dashboard/summary").json()["total_posts"] == 0
    assert client.get("/api/v1/posts/search").status_code == 422
    assert (
        client.get("/api/v1/posts/search", params={"dataset_id": str(uuid.uuid4())}).status_code
        == 404
    )
    assert (
        client.get(
            "/api/v1/posts/search",
            params={
                "dataset_id": str(dataset.id),
                "date_from": "2026-10-01",
                "date_to": "2026-09-01",
            },
        ).status_code
        == 422
    )


def test_demo_size_temporal_structure_and_patterns():
    df = pd.read_csv(io.StringIO(generate_sample_dataset()))
    assert len(df) == 900 and df["platform"].nunique() == 3
    dates = pd.to_datetime(df["created_at"], utc=True)
    assert dates.dt.normalize().nunique() == 21
    # Ground truth is generator intent, not NLP accuracy.
    label_column = "theme"
    assert label_column in df
    counts = df.groupby([df[label_column], dates.dt.day]).size().unstack(fill_value=0)
    ai = next(row for index, row in counts.iterrows() if "ai" in index.lower())
    crypto = next(row for index, row in counts.iterrows() if "crypto" in index.lower())
    health = next(row for index, row in counts.iterrows() if "health" in index.lower())
    assert ai.iloc[-5:].sum() > ai.iloc[:5].sum()
    assert crypto.iloc[-5:].sum() < crypto.iloc[:5].sum()
    assert health.iloc[-5:].sum() > health.iloc[:5].sum() * 5
    for index, row in counts.iterrows():
        if "sports" in index.lower() or "climate" in index.lower():
            assert abs(row.iloc[-5:].sum() - row.iloc[:5].sum()) < 15


def test_old_demo_requires_explicit_replacement(client, db_session):
    dataset = Dataset(
        name="Old demo",
        filename="old.csv",
        source_type="synthetic_demo",
        row_count=1535,
    )
    db_session.add(dataset)
    db_session.commit()
    response = client.post("/api/v1/datasets/sample")
    assert response.status_code == 409 and "older generator" in response.text
    assert db_session.get(Dataset, dataset.id) is not None


def test_missing_ner_is_explicit_and_never_invents_entities(monkeypatch):
    import spacy

    monkeypatch.setattr(
        spacy, "load", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("missing"))
    )
    ner = EntityRecognizer()
    assert ner.extract_from_texts(["Investors Record New Fans"]) == [[]]
    assert ner.metadata()["status"] == "unavailable" and ner.metadata()["warning"]


def test_missing_core_weights_raise_clear_errors(monkeypatch):
    import sentence_transformers
    import transformers

    def missing(*args, **kwargs):
        raise OSError("missing weights")

    monkeypatch.setattr(transformers, "pipeline", missing)
    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", missing)
    with pytest.raises(RuntimeError, match="Sentiment model .* unavailable"):
        SentimentAnalyzer().load_model()
    with pytest.raises(RuntimeError, match="Embedding model .* unavailable"):
        SentenceEmbedder().load_model()


def test_failed_model_run_is_retryable(db_session, monkeypatch):
    dataset = Dataset(name="Failure", filename="fixture.csv", source_type="csv", status="imported")
    db_session.add(dataset)
    db_session.flush()
    db_session.add(
        Post(
            dataset_id=dataset.id,
            original_text="This is a valid post",
            timestamp=datetime.now(timezone.utc),
        )
    )
    db_session.commit()
    run = create_analysis_run(db_session, dataset.id)

    def fail(*args, **kwargs):
        raise RuntimeError("Sentiment weights unavailable. Download and retry.")

    monkeypatch.setattr(SentimentAnalyzer.get_instance(), "predict_batch", fail)
    execute_analysis_run(run.id, db_session)
    assert run.status == "failed" and "Download and retry" in run.error_message
    assert create_analysis_run(db_session, dataset.id).status == "pending"
