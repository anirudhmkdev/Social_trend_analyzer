"""Tests for Phase 8: Analytics APIs (Dashboard Summary, Timeline, Search, Metadata)."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.post import Post
from app.models.topic import Topic
from app.services.analysis_service import (
    create_analysis_run,
    execute_analysis_run,
)


def test_dashboard_summary_empty(client: TestClient):
    """Test dashboard summary endpoint when no analysis runs exist."""
    res = client.get("/api/v1/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "no_data"
    assert data["total_posts"] == 0
    assert data["total_topics"] == 0
    assert data["top_trends"] == []


def test_dashboard_analytics_end_to_end(client: TestClient, db_session: Session):
    """Test full dashboard summary, timeline, and search endpoints after an analysis run."""
    # 1. Create dataset
    ds = Dataset(
        name="Analytics Test Dataset",
        filename="analytics_test.csv",
        source_type="synthetic",
        status="ready",
        row_count=20,
        column_mapping={"text": "text", "timestamp": "timestamp", "likes": "likes"},
    )
    db_session.add(ds)
    db_session.commit()

    base_time = datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    posts = []

    # Cluster 1: Machine Learning & NLP (AI Breakthroughs, 20 posts)
    for day, count in [(0, 2), (1, 6), (2, 12)]:
        cur_t = base_time + timedelta(days=day)
        for i in range(count):
            posts.append(
                Post(
                    dataset_id=ds.id,
                    original_text=f"AI and neural network breakthrough day {day} {i} #AI #Tech",
                    cleaned_text=f"ai and neural network breakthrough day {day} {i} ai tech",
                    sentiment_ready_text=f"AI breakthrough day {day} {i} #AI",
                    timestamp=cur_t + timedelta(minutes=i * 15),
                    platform="twitter" if i % 2 == 0 else "reddit",
                    author_id=f"user_{i}",
                    likes=25 + i * 5,
                    comments=5 + i,
                    shares=3 + i,
                    hashtags=["ai", "tech"],
                )
            )

    # Cluster 2: Solar Renewable Energy (12 posts)
    for day in range(3):
        cur_t = base_time + timedelta(days=day)
        for i in range(4):
            posts.append(
                Post(
                    dataset_id=ds.id,
                    original_text=f"Solar energy panels and green power day {day} {i} #Solar",
                    cleaned_text=f"solar energy panels and green power day {day} {i} solar",
                    sentiment_ready_text=f"Solar energy panels day {day} {i} #Solar",
                    timestamp=cur_t + timedelta(minutes=i * 15),
                    platform="twitter",
                    author_id=f"solar_user_{i}",
                    likes=15 + i * 2,
                    comments=2,
                    shares=1,
                    hashtags=["solar", "cleanenergy"],
                )
            )

    db_session.add_all(posts)
    db_session.commit()

    # 2. Run analysis pipeline
    run = create_analysis_run(db_session, ds.id)
    execute_analysis_run(run.id, db_session=db_session)

    # 3. Test GET /api/v1/dashboard/summary
    sum_res = client.get(f"/api/v1/dashboard/summary?analysis_run_id={run.id}")
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert sum_data["status"] == "completed"
    assert sum_data["total_posts"] == len(posts)
    assert sum_data["total_topics"] > 0
    assert "counts" in sum_data["sentiment_breakdown"]
    assert "percentages" in sum_data["sentiment_breakdown"]
    assert sum_data["sentiment_breakdown"]["total"] == len(posts)
    assert "emerging" in sum_data["trend_classifications"]
    assert "rising" in sum_data["trend_classifications"]
    assert len(sum_data["top_trends"]) > 0
    assert len(sum_data["top_hashtags"]) > 0
    assert "twitter" in sum_data["platform_breakdown"]
    assert "reddit" in sum_data["platform_breakdown"]

    # 4. Test GET /api/v1/dashboard/timeline
    time_res = client.get(f"/api/v1/dashboard/timeline?analysis_run_id={run.id}&time_window=daily")
    assert time_res.status_code == 200
    time_data = time_res.json()
    assert time_data["time_window"] == "daily"
    assert len(time_data["timeline"]) == 3  # 3 distinct days
    first_pt = time_data["timeline"][0]
    assert first_pt["total_volume"] > 0
    assert first_pt["avg_engagement"] > 0

    # 5. Test GET /api/v1/dashboard/timeline filtered by topic
    topics = db_session.query(Topic).filter(Topic.analysis_run_id == run.id).all()
    assert len(topics) > 0
    target_topic = topics[0]

    topic_time_res = client.get(
        f"/api/v1/dashboard/timeline?analysis_run_id={run.id}&topic_id={target_topic.id}"
    )
    assert topic_time_res.status_code == 200
    assert len(topic_time_res.json()["timeline"]) >= 1

    # 6. Test GET /api/v1/posts/search
    # a. Text search
    s_res = client.get(f"/api/v1/posts/search?dataset_id={ds.id}&q=breakthrough")
    assert s_res.status_code == 200
    s_data = s_res.json()
    assert s_data["total"] > 0
    assert all("breakthrough" in p["original_text"].lower() for p in s_data["items"])

    # b. Platform filter
    plat_res = client.get(f"/api/v1/posts/search?dataset_id={ds.id}&platform=reddit")
    assert plat_res.status_code == 200
    plat_data = plat_res.json()
    assert plat_data["total"] > 0
    assert all(p["platform"] == "reddit" for p in plat_data["items"])

    # c. Pagination
    page_res = client.get(f"/api/v1/posts/search?dataset_id={ds.id}&limit=5&offset=0")
    assert page_res.status_code == 200
    assert len(page_res.json()["items"]) == 5
    assert page_res.json()["total"] == len(posts)


def test_pipeline_metadata_endpoint(client: TestClient):
    """Test GET /api/v1/pipeline/metadata endpoint."""
    res = client.get("/api/v1/pipeline/metadata")
    assert res.status_code == 200
    data = res.json()
    assert data["preprocessing_version"] == "1.0.0"
    assert "MiniLM" in data["embedding_model"]
    assert data["embedding_dimensions"] == 384
    assert "roberta" in data["sentiment_model"].lower()
    assert "spacy" in data["ner_model"].lower() or "en_core_web_sm" in data["ner_model"]
    assert "BERTopic" in data["topic_model"]
    assert "volume" in data["trend_weights"]
    assert "emerging" in data["trend_thresholds"]
    assert data["database_backend"] in ("sqlite", "postgresql")
