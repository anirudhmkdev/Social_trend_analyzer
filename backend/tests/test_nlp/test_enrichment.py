"""Unit and integration tests for Phase 6: NLP Enrichment (NER, Keywords, Hashtags)."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.entity import Entity, PostEntity
from app.models.keyword_snapshot import KeywordSnapshot
from app.models.post import Post
from app.nlp.enrichment.keywords import KeywordExtractor, KeywordItem
from app.nlp.enrichment.ner import ALLOWED_ENTITY_LABELS, EntityRecognizer
from app.services.analysis_service import (
    create_analysis_run,
    execute_analysis_run,
)


def test_ner_extractor():
    ner = EntityRecognizer.get_instance()
    texts = [
        "Sam Altman announced that OpenAI will open a new office in New York.",
        "Dr. Jane Goodall discussed wildlife conservation at the UN Climate Summit in Paris.",
    ]
    results = ner.extract_from_texts(texts)
    assert len(results) == 2

    # Check entities from text 1
    doc1_ents = results[0]
    assert len(doc1_ents) >= 1
    for ent in doc1_ents:
        assert ent.label in ALLOWED_ENTITY_LABELS
        assert ent.text != ""
        assert ent.normalized_text == ent.text.lower()


def test_keyword_extractor_tfidf():
    extractor = KeywordExtractor(max_features=50)
    texts = [
        "quantum computing algorithms and qubit entanglement",
        "quantum key distribution for secure encrypted communication",
        "renewable solar photovoltaics energy storage systems",
    ]
    keywords = extractor.extract_keywords(texts, top_n=10)
    assert len(keywords) > 0
    words = [k.keyword for k in keywords]
    assert any("quantum" in w for w in words)
    for k in keywords:
        assert isinstance(k, KeywordItem)
        assert k.frequency >= 1
        assert k.tfidf_score is not None


def test_hashtag_analyzer_and_growth():
    extractor = KeywordExtractor()
    hashtag_lists = [
        ["AI", "tech"],
        ["AI", "MachineLearning"],
        ["AI", "DeepLearning"],
        ["AI", "DeepLearning", "NewTopic"],
    ]
    results = extractor.analyze_hashtags(hashtag_lists, period_split_index=2)
    assert len(results) >= 3
    tags = {h.keyword: h for h in results}
    assert "AI" in tags
    assert tags["AI"].frequency == 4


def test_enrichment_pipeline_db_persistence(db_session: Session):
    dataset = Dataset(
        name="Enrichment DB Dataset",
        filename="enrich.csv",
        source_type="csv",
        status="uploaded",
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    posts = [
        Post(
            dataset_id=dataset.id,
            original_text="Google and DeepMind published in Paris. #AI #Innovation",
            timestamp=datetime.now(timezone.utc),
        ),
        Post(
            dataset_id=dataset.id,
            original_text="Microsoft expanded Azure infrastructure in Europe. #Cloud #Innovation",
            timestamp=datetime.now(timezone.utc),
        ),
    ]
    db_session.add_all(posts)
    db_session.commit()

    run = create_analysis_run(db_session, dataset.id)
    execute_analysis_run(run.id, db_session=db_session)

    db_session.refresh(run)
    assert run.status == "completed"
    assert "enrichment" in run.stats

    # Check entities in DB
    entities = db_session.query(Entity).filter(Entity.analysis_run_id == run.id).all()
    assert len(entities) >= 1

    post_entities = db_session.query(PostEntity).filter(PostEntity.analysis_run_id == run.id).all()
    assert len(post_entities) >= 1

    # Check keywords in DB
    kw_records = (
        db_session.query(KeywordSnapshot)
        .filter(KeywordSnapshot.analysis_run_id == run.id)
        .all()
    )
    assert len(kw_records) >= 1


def test_enrichment_api_endpoints(client: TestClient, db_session: Session):
    dataset = Dataset(
        name="API Enrichment Dataset",
        filename="api_enrich.csv",
        source_type="csv",
        status="uploaded",
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    posts = [
        Post(
            dataset_id=dataset.id,
            original_text="Meta released open source models in New York. #OpenSource #Tech",
            timestamp=datetime.now(timezone.utc),
        ),
        Post(
            dataset_id=dataset.id,
            original_text="OpenAI researchers presented in Tokyo. #AI #Tech",
            timestamp=datetime.now(timezone.utc),
        ),
    ]
    db_session.add_all(posts)
    db_session.commit()

    run = create_analysis_run(db_session, dataset.id)
    execute_analysis_run(run.id, db_session=db_session)

    # 1. GET /api/v1/enrichment/entities
    res_ent = client.get(f"/api/v1/enrichment/entities?analysis_run_id={run.id}")
    assert res_ent.status_code == 200
    ent_data = res_ent.json()
    assert "entities" in ent_data
    assert "by_type" in ent_data

    # 2. GET /api/v1/enrichment/keywords
    res_kw = client.get(f"/api/v1/enrichment/keywords?analysis_run_id={run.id}")
    assert res_kw.status_code == 200
    kw_data = res_kw.json()
    assert "items" in kw_data

    # 3. GET /api/v1/enrichment/hashtags
    res_ht = client.get(f"/api/v1/enrichment/hashtags?analysis_run_id={run.id}")
    assert res_ht.status_code == 200
    ht_data = res_ht.json()
    assert "hashtags" in ht_data
