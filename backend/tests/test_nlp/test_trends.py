"""Tests for Phase 7: Trend Detection Engine."""

import math
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.post import Post
from app.models.topic import Topic
from app.nlp.trends.aggregator import (
    TemporalAggregator,
    get_utc_window_end,
    get_utc_window_start,
)
from app.nlp.trends.config import TrendConfig
from app.nlp.trends.scoring import (
    classify_trend,
    compute_base_momentum,
    compute_recency,
    compute_trend_score,
    generate_explanation,
    logistic_normalize,
)
from app.services.analysis_service import create_analysis_run, execute_analysis_run

# ============================================================================
# Unit Tests: Mathematical Scoring & Invariants
# ============================================================================


def test_logistic_normalize_neutral():
    """Verify S(0) == 0.50 for centered logistic normalization."""
    assert logistic_normalize(0.0) == 0.50
    assert logistic_normalize(0) == 0.50


def test_logistic_normalize_bounds_and_steepness():
    """Verify bounds in (0, 1) and positive/negative directionality."""
    pos = logistic_normalize(2.0, k=1.0)
    neg = logistic_normalize(-2.0, k=1.0)
    assert 0.5 < pos < 1.0
    assert 0.0 < neg < 0.5
    # Symmetry around 0.5
    assert abs((pos - 0.5) - (0.5 - neg)) < 1e-6


def test_no_growth_case_mathematical_neutral():
    """Mathematical Guarantee: Zero growth produces M_base=0.50, TrendScore=0.50, Stable."""
    config = TrendConfig()
    norm_vol = logistic_normalize(0.0)
    norm_eng = logistic_normalize(0.0)
    norm_vel = logistic_normalize(0.0)
    norm_burst = logistic_normalize(0.0)

    # Base momentum should be precisely 0.50
    m_base = compute_base_momentum(
        norm_vol, norm_eng, norm_vel, norm_burst, has_engagement=True, config=config
    )
    assert abs(m_base - 0.50) < 1e-6

    # Regardless of recency R, TrendScore must remain 0.50
    for r in [1.0, 0.8, 0.5, 0.1, 0.01]:
        score = compute_trend_score(m_base, r)
        assert abs(score - 0.50) < 1e-6

    # Classification must be 'stable'
    classification = classify_trend(
        trend_score=0.50,
        volume_current=15,
        volume_previous=15,
        topic_age_windows=3,
        min_posts=3,
        config=config,
    )
    assert classification == "stable"


def test_rising_trend_case():
    """Verify rising classification for high momentum (> 0.60) and non-emerging topic."""
    config = TrendConfig()
    norm_vol = logistic_normalize(3.0)  # Strong positive growth
    norm_eng = logistic_normalize(2.0)
    norm_vel = logistic_normalize(1.5)
    norm_burst = logistic_normalize(2.0)

    m_base = compute_base_momentum(
        norm_vol, norm_eng, norm_vel, norm_burst, has_engagement=True, config=config
    )
    assert m_base > 0.70

    recency = 0.95
    score = compute_trend_score(m_base, recency)
    assert score >= 0.60

    classification = classify_trend(
        trend_score=score,
        volume_current=50,
        volume_previous=20,
        topic_age_windows=5,  # Established topic
        min_posts=3,
        config=config,
    )
    assert classification == "rising"


def test_declining_trend_case():
    """Verify declining classification for negative momentum (< 0.40)."""
    config = TrendConfig()
    norm_vol = logistic_normalize(-3.0)  # Strong decline
    norm_eng = logistic_normalize(-2.0)
    norm_vel = logistic_normalize(-1.5)
    norm_burst = logistic_normalize(-1.0)

    m_base = compute_base_momentum(
        norm_vol, norm_eng, norm_vel, norm_burst, has_engagement=True, config=config
    )
    assert m_base < 0.35

    recency = 0.90
    score = compute_trend_score(m_base, recency)
    assert score < config.threshold_stable  # < 0.40

    classification = classify_trend(
        trend_score=score,
        volume_current=10,
        volume_previous=40,
        topic_age_windows=4,
        min_posts=3,
        config=config,
    )
    assert classification == "declining"


def test_emerging_from_zero_case():
    """Verify emerging classification when score >= 0.70 and volume_prev=0 or age<2."""
    config = TrendConfig()

    # Topic appearing newly with high score
    classification_new = classify_trend(
        trend_score=0.78,
        volume_current=25,
        volume_previous=0,  # Appeared from zero
        topic_age_windows=1,
        min_posts=3,
        config=config,
    )
    assert classification_new == "emerging"

    # Same score on an older established topic with continuous volume should be 'rising'
    classification_est = classify_trend(
        trend_score=0.78,
        volume_current=25,
        volume_previous=15,
        topic_age_windows=4,
        min_posts=3,
        config=config,
    )
    assert classification_est == "rising"


def test_tiny_sample_guard():
    """Verify samples with volume < min_posts are classified as stable to avoid spurious spikes."""
    config = TrendConfig(min_posts_for_trend=3)
    classification = classify_trend(
        trend_score=0.95,  # High score
        volume_current=2,  # Too few posts
        volume_previous=0,
        topic_age_windows=1,
        min_posts=3,
        config=config,
    )
    assert classification == "stable"


def test_missing_engagement_vs_genuine_zero():
    """Verify engagement redistribution when unmapped vs genuine zero engagement."""
    config = TrendConfig()

    # Genuine zero engagement (e_g = 0 -> S(0) = 0.50)
    m_with_zero_eng = compute_base_momentum(
        norm_vol=0.8,
        norm_eng=0.5,  # Genuine 0 mapped
        norm_vel=0.8,
        norm_burst=0.8,
        has_engagement=True,
        config=config,
    )
    # 0.35*0.8 + 0.25*0.5 + 0.20*0.8 + 0.20*0.8 = 0.28 + 0.125 + 0.16 + 0.16 = 0.725
    assert abs(m_with_zero_eng - 0.725) < 1e-4

    # Unmapped engagement (has_engagement=False)
    m_unmapped = compute_base_momentum(
        norm_vol=0.8,
        norm_eng=0.0,
        norm_vel=0.8,
        norm_burst=0.8,
        has_engagement=False,
        config=config,
    )
    # Weights redistributed proportionally across non-eng: sum = 0.75, each scaled by 1/0.75
    # (0.35/0.75)*0.8 + (0.20/0.75)*0.8 + (0.20/0.75)*0.8 = 0.8
    assert abs(m_unmapped - 0.80) < 1e-4


def test_recency_decay():
    """Verify exponential recency decay R = exp(-lambda * delta_t)."""
    now = datetime(2026, 8, 10, 12, 0, 0, tzinfo=timezone.utc)
    t0 = now
    t_12h = now - timedelta(hours=12)
    t_24h = now - timedelta(hours=24)

    r0 = compute_recency(t0, now, decay_rate=0.05)
    r_12h = compute_recency(t_12h, now, decay_rate=0.05)
    r_24h = compute_recency(t_24h, now, decay_rate=0.05)

    assert abs(r0 - 1.0) < 1e-6
    assert 0.0 < r_24h < r_12h < 1.0
    assert abs(r_12h - math.exp(-0.05 * 12)) < 1e-5


def test_explanation_generation():
    """Verify human-readable explanation with explicit standard deviations for burstiness."""
    record = {
        "volume": 50,
        "volume_previous": 20,
        "volume_growth_pct": 150.0,
        "burst_score": 2.85,
        "avg_engagement": 35.4,
    }
    exp = generate_explanation(record)
    assert "Post volume increased by 150%" in exp
    assert "2.9 standard deviations above the historical baseline" in exp


# ============================================================================
# Unit Tests: Aggregator & Temporal Windows
# ============================================================================


def test_temporal_aggregator_utc_alignment():
    """Verify UTC calendar boundaries for daily and hourly windows."""
    dt = datetime(2026, 8, 10, 15, 43, 22, tzinfo=timezone.utc)
    daily_start = get_utc_window_start(dt, "daily")
    assert daily_start == datetime(2026, 8, 10, 0, 0, 0, tzinfo=timezone.utc)

    daily_end = get_utc_window_end(daily_start, "daily")
    assert daily_end == datetime(2026, 8, 11, 0, 0, 0, tzinfo=timezone.utc)

    hourly_start = get_utc_window_start(dt, "hourly")
    assert hourly_start == datetime(2026, 8, 10, 15, 0, 0, tzinfo=timezone.utc)


def test_aggregator_trajectory():
    """Verify aggregator trajectory computes growth, velocity, and burstiness correctly."""
    agg = TemporalAggregator(time_window="daily")
    t0 = datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 8, 2, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 3, 10, 0, 0, tzinfo=timezone.utc)

    posts_data = [
        {"timestamp": t0, "likes": 5, "comments": 2, "shares": 1, "sentiment": "positive"},
        {"timestamp": t0, "likes": 3, "comments": 1, "shares": 0, "sentiment": "neutral"},
        # Day 2: 4 posts
        {"timestamp": t1, "likes": 10, "comments": 5, "shares": 2, "sentiment": "positive"},
        {"timestamp": t1, "likes": 12, "comments": 3, "shares": 1, "sentiment": "positive"},
        {"timestamp": t1, "likes": 8, "comments": 2, "shares": 1, "sentiment": "positive"},
        {"timestamp": t1, "likes": 15, "comments": 4, "shares": 2, "sentiment": "negative"},
        # Day 3: 8 posts
        *[
            {"timestamp": t2, "likes": 20, "comments": 5, "shares": 5, "sentiment": "positive"}
            for _ in range(8)
        ],
    ]

    windows = agg.group_posts_by_window(posts_data)
    assert len(windows) == 3

    metrics_list = []
    for w_start, p_list in windows.items():
        m = agg.compute_window_metrics(p_list, has_engagement=True)
        metrics_list.append(
            {
                "window_start": w_start,
                "window_end": get_utc_window_end(w_start, "daily"),
                **m,
            }
        )

    trajectory = agg.compute_trajectory(metrics_list, min_baseline=1.0)
    assert len(trajectory) == 3

    # Day 2 should show positive growth from Day 1
    assert trajectory[1]["volume_growth"] > 0
    # Day 3 should show positive velocity
    assert trajectory[2]["volume"] == 8


# ============================================================================
# Integration Tests: End-to-End Pipeline & API Endpoints
# ============================================================================


def test_trend_engine_end_to_end_analysis(db_session: Session):
    """Test full analysis run execution generates trend snapshots stored in DB."""
    # Create dataset
    ds = Dataset(
        name="Trend Test Dataset",
        filename="trend_test.csv",
        source_type="synthetic",
        status="ready",
        row_count=30,
        column_mapping={"text": "text", "timestamp": "timestamp", "likes": "likes"},
    )
    db_session.add(ds)
    db_session.commit()

    # Create posts across 3 consecutive days for 2 distinct themes
    base_time = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
    posts = []

    # Theme A: AI Breakthroughs (growing from 2 -> 6 -> 12 posts)
    for day, count in [(0, 2), (1, 6), (2, 12)]:
        cur_time = base_time + timedelta(days=day)
        for i in range(count):
            p = Post(
                dataset_id=ds.id,
                original_text=f"AI and neural network breakthrough day {day} {i} #AI #Tech",
                cleaned_text=f"ai and neural network breakthrough day {day} {i} ai tech",
                sentiment_ready_text=f"AI breakthrough day {day} {i} #AI",
                timestamp=cur_time + timedelta(minutes=i * 10),
                platform="twitter",
                likes=15 + i * 5,
                comments=3 + i,
                shares=2 + i,
                hashtags=["ai", "tech"],
            )
            posts.append(p)

    # Theme B: Solar Renewable Energy
    for day in range(3):
        cur_time = base_time + timedelta(days=day)
        for i in range(4):
            p = Post(
                dataset_id=ds.id,
                original_text=f"Solar energy panels and green power day {day} {i} #Solar",
                cleaned_text=f"solar energy panels and green power day {day} {i} solar",
                sentiment_ready_text=f"Solar energy panels day {day} {i} #Solar",
                timestamp=cur_time + timedelta(minutes=i * 15),
                platform="twitter",
                likes=10 + i * 2,
                comments=2,
                shares=1,
                hashtags=["solar"],
            )
            posts.append(p)

    db_session.add_all(posts)
    db_session.commit()

    # Create and execute AnalysisRun
    run = create_analysis_run(db_session, ds.id)
    execute_analysis_run(run.id, db_session=db_session)

    # Reload run
    db_session.refresh(run)
    assert run.status == "completed"
    assert "trends" in run.stats
    assert run.stats["trends"]["total_snapshots"] > 0
    assert run.stats["trends"]["topics_evaluated"] > 0

    # Verify TrendSnapshots exist in database
    topics = (
        db_session.query(Topic)
        .filter(Topic.analysis_run_id == run.id, Topic.is_outlier.is_(False))
        .all()
    )
    assert len(topics) > 0


def test_trend_api_endpoints(client: TestClient, db_session: Session):
    """Test GET /api/v1/trends and GET /api/v1/trends/topic/{topic_id} endpoints."""
    # Create dataset and posts
    ds = Dataset(
        name="API Trend Dataset",
        filename="api_trend.csv",
        source_type="synthetic",
        status="ready",
        row_count=20,
        column_mapping={"text": "text", "timestamp": "timestamp"},
    )
    db_session.add(ds)
    db_session.commit()

    t0 = datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    posts = []
    # Theme A: Quantum Computing
    for day in range(3):
        cur_t = t0 + timedelta(days=day)
        for i in range(5):
            posts.append(
                Post(
                    dataset_id=ds.id,
                    original_text=f"Quantum computing qubit circuits day {day} {i} #Quantum",
                    cleaned_text=f"quantum computing qubit circuits day {day} {i} quantum",
                    sentiment_ready_text=f"Quantum computing day {day} {i} #Quantum",
                    timestamp=cur_t + timedelta(hours=i * 2),
                    platform="twitter",
                    likes=20 + i * 5,
                    comments=4 + i,
                    shares=2 + i,
                    hashtags=["quantum"],
                )
            )
    # Theme B: Solar Renewable Energy
    for day in range(3):
        cur_t = t0 + timedelta(days=day)
        for i in range(5):
            posts.append(
                Post(
                    dataset_id=ds.id,
                    original_text=f"Solar energy panels and clean power day {day} {i} #Solar",
                    cleaned_text=f"solar energy panels and clean power day {day} {i} solar",
                    sentiment_ready_text=f"Solar energy panels day {day} {i} #Solar",
                    timestamp=cur_t + timedelta(hours=i * 2),
                    platform="twitter",
                    likes=15 + i * 3,
                    comments=3,
                    shares=1,
                    hashtags=["solar", "cleanenergy"],
                )
            )
    db_session.add_all(posts)
    db_session.commit()

    run = create_analysis_run(db_session, ds.id)
    execute_analysis_run(run.id, db_session=db_session)

    db_session.refresh(run)
    assert run.status == "completed", f"Run failed with error: {run.error_message}"
    assert run.stats["trends"]["total_snapshots"] > 0

    # 1. GET /api/v1/trends
    res = client.get(f"/api/v1/trends?analysis_run_id={run.id}")
    assert res.status_code == 200
    data = res.json()
    assert "trends" in data
    assert "total" in data
    assert data["total"] > 0
    assert "emerging_count" in data
    assert "rising_count" in data
    assert "stable_count" in data
    assert "declining_count" in data

    first_trend = data["trends"][0]
    assert "trend_score" in first_trend
    assert "classification" in first_trend
    assert "explanation" in first_trend
    assert "volume_current" in first_trend
    assert 0.0 <= first_trend["trend_score"] <= 1.0

    topic_id = first_trend["topic_id"]

    # 2. GET /api/v1/trends/topic/{topic_id}
    res_topic = client.get(f"/api/v1/trends/topic/{topic_id}")
    assert res_topic.status_code == 200
    trajectory_data = res_topic.json()
    assert isinstance(trajectory_data, list)
    assert len(trajectory_data) >= 1
    assert trajectory_data[0]["topic_id"] == topic_id
