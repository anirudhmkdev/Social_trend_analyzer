"""Unit tests for Phase 3 NLP Preprocessing."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.post import Post
from app.nlp.preprocessing.cleaner import (
    PREPROCESSING_VERSION,
    TextPreprocessor,
)
from app.nlp.preprocessing.pipeline import run_dataset_preprocessing


def test_empty_text():
    preprocessor = TextPreprocessor()
    res = preprocessor.process("")
    assert res.original_text == ""
    assert res.cleaned_text == ""
    assert res.sentiment_ready_text == ""
    assert res.hashtags == []
    assert res.mentions == []
    assert res.urls == []
    assert res.is_duplicate is False

    res_none = preprocessor.process(None)
    assert res_none.cleaned_text == ""
    assert res_none.sentiment_ready_text == ""


def test_hashtag_extraction_and_cleaning():
    preprocessor = TextPreprocessor()
    text = "Great breakthrough in #ArtificialIntelligence and #NLP! #tech"
    res = preprocessor.process(text)

    # Hashtags extracted with casing preserved, without #
    assert "ArtificialIntelligence" in res.hashtags
    assert "NLP" in res.hashtags
    assert "tech" in res.hashtags

    # Cleaned text has # stripped but token retained, lowercased
    assert "artificialintelligence" in res.cleaned_text
    assert "nlp" in res.cleaned_text
    assert "tech" in res.cleaned_text
    assert "#" not in res.cleaned_text

    # Sentiment ready text retains #
    assert (
        "#ArtificialIntelligence" in res.sentiment_ready_text
        or "ArtificialIntelligence" in res.sentiment_ready_text
    )


def test_mention_extraction_and_normalization():
    preprocessor = TextPreprocessor()
    text = "Hey @elonmusk check with @OpenAI about this update!"
    res = preprocessor.process(text)

    # Mentions extracted
    assert "elonmusk" in res.mentions
    assert "OpenAI" in res.mentions

    # sentiment_ready_text has @user replacements, casing preserved
    assert "@user check with @user about this update!" in res.sentiment_ready_text

    # cleaned_text removes mentions and lowercases
    assert "elonmusk" not in res.cleaned_text
    assert "openai" not in res.cleaned_text
    assert "check with about this update!" in res.cleaned_text


def test_url_extraction_and_normalization():
    preprocessor = TextPreprocessor()
    text = "Read the report https://example.com/research/paper?id=123 and www.demo.org/news now"
    res = preprocessor.process(text)

    assert len(res.urls) == 2
    assert "https://example.com/research/paper?id=123" in res.urls

    # sentiment_ready_text replaces URLs with http
    assert "read the report http and http now".lower() == res.sentiment_ready_text.lower()

    # cleaned_text removes URLs entirely
    assert "http" not in res.cleaned_text
    assert "example.com" not in res.cleaned_text
    assert "read the report and now" in res.cleaned_text


def test_html_entities_decoding():
    preprocessor = TextPreprocessor()
    text = "Machine Learning &amp; AI &lt;Deep Learning&gt; &quot;State of the Art&quot;"
    res = preprocessor.process(text)

    assert "&amp;" not in res.cleaned_text
    assert "&lt;" not in res.cleaned_text
    assert "&" in res.cleaned_text or "machine learning" in res.cleaned_text
    assert '"state of the art"' in res.cleaned_text or "state of the art" in res.cleaned_text


def test_punctuation_collapsing():
    preprocessor = TextPreprocessor()
    text = "Incredible discovery!!!!!!!! Are you sure?????? Yes......"
    res = preprocessor.process(text)

    assert "!!!!!!" not in res.cleaned_text
    assert "!" in res.cleaned_text
    assert "????" not in res.cleaned_text
    assert "?" in res.cleaned_text
    assert "......" not in res.cleaned_text


def test_emoji_and_unicode_handling():
    preprocessor = TextPreprocessor()
    text = "Solar energy breakthrough! ☀️🚀🌍 Ça marche très bien à Paris — 100%!"
    res = preprocessor.process(text)

    # Unicode accents preserved in cleaned text, lowercased
    assert "ça marche très bien à paris" in res.cleaned_text
    # Original text preserved
    assert res.original_text == text


def test_duplicate_text_detection():
    preprocessor = TextPreprocessor()
    seen = set()

    text1 = "Excited about the new quantum computing research papers."
    text2 = "  excited about  the NEW quantum computing research papers.  "
    text3 = "Different post altogether!"

    res1 = preprocessor.process(text1, seen_hashes=seen)
    res2 = preprocessor.process(text2, seen_hashes=seen)
    res3 = preprocessor.process(text3, seen_hashes=seen)

    assert res1.is_duplicate is False
    assert res2.is_duplicate is True
    assert res3.is_duplicate is False


def test_runtime_ner_text_derivation():
    text = "Dr. Jane Smith visited Google HQ in New York! Read at https://tech.io/report."
    ner_text = TextPreprocessor.derive_ner_text(text)

    # Preserves casing
    assert "Dr. Jane Smith" in ner_text
    assert "Google HQ" in ner_text
    assert "New York" in ner_text
    # Removes URL
    assert "https://" not in ner_text
    assert "tech.io" not in ner_text


def test_dataset_preprocessing_pipeline(db_session: Session):
    # Setup dataset with posts
    dataset = Dataset(
        name="Test Preprocessing Dataset",
        filename="test.csv",
        source_type="csv",
        row_count=3,
        valid_row_count=3,
        status="uploaded",
    )
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)

    p1 = Post(
        dataset_id=dataset.id,
        original_text="Check out #AI developments at https://ai.org with @researcher!",
        timestamp=datetime.now(timezone.utc),
    )
    p2 = Post(
        dataset_id=dataset.id,
        original_text="Check out #AI developments at https://ai.org with @researcher!",
        timestamp=datetime.now(timezone.utc),
    )
    p3 = Post(
        dataset_id=dataset.id,
        original_text="A completely unique message about #RenewableEnergy.",
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add_all([p1, p2, p3])
    db_session.commit()

    # Run preprocessing
    summary = run_dataset_preprocessing(db_session, dataset.id)

    assert summary["posts_processed"] == 3
    assert summary["duplicates_count"] == 1
    assert summary["preprocessing_version"] == PREPROCESSING_VERSION
    assert summary["status"] == "preprocessed"
    assert summary["reused_canonical"] is False

    # Check post values in db
    db_session.refresh(p1)
    db_session.refresh(p2)
    db_session.refresh(p3)

    assert p1.cleaned_text is not None
    assert "ai developments" in p1.cleaned_text
    assert "ai.org" not in p1.cleaned_text
    assert "@researcher" not in p1.cleaned_text
    assert p1.sentiment_ready_text is not None
    assert "@user" in p1.sentiment_ready_text
    assert "http" in p1.sentiment_ready_text
    assert p1.hashtags == ["AI"]
    assert p1.mentions == ["researcher"]
    assert p1.urls == ["https://ai.org"]
    assert p1.is_duplicate is False

    # p2 is duplicate of p1
    assert p2.is_duplicate is True

    # Idempotent second run reuses canonical representation
    summary2 = run_dataset_preprocessing(db_session, dataset.id)
    assert summary2["reused_canonical"] is True
