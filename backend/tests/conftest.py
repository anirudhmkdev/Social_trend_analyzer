import os
import sys
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app.models  # noqa: E402, F401
from app.database.base import Base  # noqa: E402
from app.database.engine import get_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402

# In-memory SQLite database for isolated test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db_session: Session, monkeypatch) -> Generator[TestClient, None, None]:
    import app.main as main_module
    from app.api.v1.endpoints import analysis
    from app.services.analysis_service import execute_analysis_run

    # Background tasks use the same isolated transaction as the HTTP request.
    monkeypatch.setattr(main_module, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(
        analysis,
        "execute_analysis_run",
        lambda run_id: execute_analysis_run(run_id, db_session=db_session),
    )

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def isolated_inference_and_uploads(monkeypatch, tmp_path):
    from app.config import settings
    from app.nlp.enrichment.ner import EntityRecognizer
    from app.nlp.sentiment.classifier import SentimentAnalyzer
    from app.nlp.topics.embedder import SentenceEmbedder
    from tests.model_fixtures import install_model_fixtures

    for cls in [EntityRecognizer, SentimentAnalyzer, SentenceEmbedder]:
        monkeypatch.setattr(cls, "_instance", None)
    install_model_fixtures()
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
