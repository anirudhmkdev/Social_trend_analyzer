"""Unit and integration tests for Phase 5: Topic Modeling."""

from datetime import datetime, timezone

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.post import Post
from app.models.topic import PostTopic, Topic
from app.nlp.topics.embedder import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL_NAME,
    SentenceEmbedder,
)
from app.nlp.topics.modeler import (
    DiscoveredTopic,
    TopicModeler,
    generate_topic_name,
)
from app.services.analysis_service import (
    create_analysis_run,
    execute_analysis_run,
)


def test_sentence_embedder_dimensions_and_normalization():
    embedder = SentenceEmbedder.get_instance()
    assert embedder.dimensions == EMBEDDING_DIMENSIONS
    assert embedder.model_name == EMBEDDING_MODEL_NAME

    texts = [
        "Artificial intelligence and deep learning models.",
        "Renewable wind energy and solar photovoltaic cells.",
    ]
    vecs = embedder.encode(texts, normalize_embeddings=True)
    assert isinstance(vecs, np.ndarray)
    assert vecs.shape == (2, EMBEDDING_DIMENSIONS)

    # Check L2 normalization (unit length)
    for v in vecs:
        norm = np.linalg.norm(v)
        assert pytest.approx(norm, abs=1e-3) == 1.0


def test_sentence_embedder_empty_input():
    embedder = SentenceEmbedder.get_instance()
    vecs = embedder.encode([])
    assert vecs.shape == (0, EMBEDDING_DIMENSIONS)


def test_topic_naming_utility():
    kw = [{"word": "climate"}, {"word": "emissions"}, {"word": "renewable"}]
    name = generate_topic_name(kw, 0)
    assert name == "Renewable Energy"

    kw_two = [{"word": "crypto"}, {"word": "bitcoin"}]
    assert generate_topic_name(kw_two, 1) == "Crypto Markets"

    kw_one = [{"word": "sports"}]
    assert generate_topic_name(kw_one, 2) == "Sports Competition"

    # Outlier naming
    assert generate_topic_name([], -1) == "Unclassified (Outliers)"


def test_topic_modeler_clustering():
    modeler = TopicModeler(random_state=42)
    docs = [
        "Solar power energy transition and net zero targets",
        "Wind turbines generating renewable green electricity",
        "Deep learning transformer models in artificial intelligence",
        "Neural network training algorithms for language models",
        "Bitcoin and cryptocurrency blockchain market volatility",
        "Ethereum smart contracts and decentralized finance protocols",
    ]
    labels, probs, topics = modeler.fit_transform(docs)

    assert len(labels) == len(docs)
    assert len(probs) == len(docs)
    assert len(topics) >= 1
    for t in topics:
        assert isinstance(t, DiscoveredTopic)
        assert t.display_name != ""
        assert len(t.post_indices) > 0


def test_topic_pipeline_and_db_persistence(db_session: Session):
    dataset = Dataset(
        name="Topic Test Dataset",
        filename="topics.csv",
        source_type="csv",
        status="imported",
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    posts = [
        Post(
            dataset_id=dataset.id,
            original_text="Solar panel installations breaking records in Europe.",
            timestamp=datetime.now(timezone.utc),
        ),
        Post(
            dataset_id=dataset.id,
            original_text="Wind energy investments grow as clean power demand expands.",
            timestamp=datetime.now(timezone.utc),
        ),
        Post(
            dataset_id=dataset.id,
            original_text="New neural networks achieve state of the art accuracy in NLP.",
            timestamp=datetime.now(timezone.utc),
        ),
    ]
    db_session.add_all(posts)
    db_session.commit()

    run = create_analysis_run(db_session, dataset.id)
    execute_analysis_run(run.id, db_session=db_session)

    db_session.refresh(run)
    assert run.status == "completed"
    assert "topics" in run.stats
    assert run.model_info is not None
    assert run.model_info["embedding_dimensions"] == EMBEDDING_DIMENSIONS

    # Check topics table
    db_topics = db_session.query(Topic).filter(Topic.analysis_run_id == run.id).all()
    assert len(db_topics) >= 1

    # Check post_topics junction table
    post_topics = db_session.query(PostTopic).filter(PostTopic.analysis_run_id == run.id).all()
    assert len(post_topics) == len(posts)


def test_topics_api_endpoints(client: TestClient, db_session: Session):
    dataset = Dataset(
        name="API Topics Dataset",
        filename="api_topics.csv",
        source_type="csv",
        status="imported",
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    posts = [
        Post(
            dataset_id=dataset.id,
            original_text="Artificial intelligence advancements in medical diagnostics.",
            timestamp=datetime.now(timezone.utc),
        ),
        Post(
            dataset_id=dataset.id,
            original_text="Machine learning models improving renewable battery storage.",
            timestamp=datetime.now(timezone.utc),
        ),
    ]
    db_session.add_all(posts)
    db_session.commit()

    run = create_analysis_run(db_session, dataset.id)
    execute_analysis_run(run.id, db_session=db_session)

    # 1. GET /api/v1/topics
    resp = client.get(f"/api/v1/topics?analysis_run_id={run.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "topics" in data
    assert len(data["topics"]) >= 1

    topic_id = data["topics"][0]["id"]

    # 2. GET /api/v1/topics/{topic_id}
    detail_resp = client.get(f"/api/v1/topics/{topic_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["topic"]["id"] == topic_id
    assert "sentiment_distribution" in detail_data
    assert "avg_engagement" in detail_data
    assert "sample_posts" in detail_data
