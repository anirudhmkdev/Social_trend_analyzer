import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.post import Post


def test_create_dataset_and_post(db_session: Session) -> None:
    now_utc = datetime.now(timezone.utc)
    dataset = Dataset(
        name="Test Dataset",
        filename="test.csv",
        source_type="csv",
        row_count=1,
        valid_row_count=1,
        preprocessing_version="1.0.0",
        status="uploaded",
        column_mapping={"text": "text", "timestamp": "timestamp"},
        validation_results={"valid": True, "duplicate_count": 0},
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    assert dataset.id is not None
    assert isinstance(dataset.id, uuid.UUID)
    assert dataset.name == "Test Dataset"
    assert dataset.preprocessing_version == "1.0.0"

    post = Post(
        dataset_id=dataset.id,
        external_id="ext-001",
        original_text="Hello world! Real-time NLP test.",
        cleaned_text="hello world real-time nlp test",
        sentiment_ready_text="Hello world! Real-time NLP test.",
        timestamp=now_utc,
        platform="twitter",
        likes=10,
        comments=2,
        shares=1,
        hashtags=["nlp", "test"],
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    assert post.id is not None
    assert post.dataset_id == dataset.id
    assert post.dataset.name == "Test Dataset"
    assert len(dataset.posts) == 1
    assert dataset.posts[0].original_text == "Hello world! Real-time NLP test."
