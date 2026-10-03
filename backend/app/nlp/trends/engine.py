"""Trend detection engine coordinating temporal aggregation and scoring."""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.nlp.trends.aggregator import (
    TemporalAggregator,
    get_utc_window_end,
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

logger = logging.getLogger(__name__)


@dataclass
class ComputedTrendSnapshot:
    topic_id: uuid.UUID
    time_window: str
    window_start: datetime
    window_end: datetime
    trend_score: float
    classification: str
    explanation: str
    volume_current: int
    volume_previous: int
    volume_growth_pct: Optional[float]
    engagement_current: Optional[float]
    engagement_previous: Optional[float]
    engagement_growth_pct: Optional[float]
    velocity: Optional[float]
    burst_score: Optional[float]
    recency_score: Optional[float]
    sentiment_positive_pct: Optional[float]
    sentiment_neutral_pct: Optional[float]
    sentiment_negative_pct: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TrendEngine:
    """Core trend detection engine adhering to mathematical specifications."""

    def __init__(self, config: Optional[TrendConfig] = None):
        self.config = config or TrendConfig()
        self.aggregator = TemporalAggregator(time_window=self.config.time_window)

    def analyze_topic(
        self,
        topic_id: uuid.UUID,
        posts_data: List[Dict[str, Any]],
        now_utc: Optional[datetime] = None,
        has_engagement: bool = True,
    ) -> List[ComputedTrendSnapshot]:
        """Analyze temporal posts for a single topic and return trend snapshots."""
        if not posts_data:
            return []

        if now_utc is None:
            now_utc = datetime.now(timezone.utc)

        # Step 1: Group posts into UTC windows
        windows_map = self.aggregator.group_posts_by_window(posts_data)

        # Step 2: Metrics per window
        window_starts = list(windows_map.keys())
        raw_metrics_list = []
        for w_start in window_starts:
            posts_in_w = windows_map[w_start]
            metrics = self.aggregator.compute_window_metrics(
                posts_in_w, has_engagement=has_engagement
            )
            raw_metrics_list.append(
                {
                    "window_start": w_start,
                    "window_end": get_utc_window_end(w_start, self.config.time_window),
                    **metrics,
                }
            )

        # Step 3: Trajectory across windows (growth, velocity, burstiness)
        trajectory = self.aggregator.compute_trajectory(
            raw_metrics_list, min_baseline=self.config.min_baseline
        )

        snapshots: List[ComputedTrendSnapshot] = []

        for window_rec in trajectory:
            w_start = window_rec["window_start"]
            w_end = window_rec["window_end"]

            vol_growth = window_rec["volume_growth"]
            eng_growth = window_rec["engagement_growth"]
            velocity = window_rec["velocity"]
            burst_z = window_rec["burst_score"]

            # Centered logistic normalization for each signal
            norm_vol = logistic_normalize(vol_growth, k=self.config.logistic_k)
            norm_eng = logistic_normalize(eng_growth, k=self.config.logistic_k)
            norm_vel = logistic_normalize(velocity, k=self.config.logistic_k)
            norm_burst = logistic_normalize(burst_z, k=self.config.burst_logistic_k)

            base_momentum = compute_base_momentum(
                norm_vol=norm_vol,
                norm_eng=norm_eng,
                norm_vel=norm_vel,
                norm_burst=norm_burst,
                has_engagement=has_engagement,
                config=self.config,
            )

            latest_post_time = window_rec.get("latest_post_time") or w_end
            recency = compute_recency(
                latest_post_time_utc=latest_post_time,
                now_utc=now_utc,
                decay_rate=self.config.decay_rate,
            )

            trend_score = compute_trend_score(base_momentum, recency)

            classification = classify_trend(
                trend_score=trend_score,
                volume_current=window_rec["volume"],
                volume_previous=window_rec["volume_previous"],
                topic_age_windows=window_rec["topic_age_windows"],
                min_posts=self.config.min_posts_for_trend,
                config=self.config,
            )

            explanation = generate_explanation(window_rec)

            snap = ComputedTrendSnapshot(
                topic_id=topic_id,
                time_window=self.config.time_window,
                window_start=w_start,
                window_end=w_end,
                trend_score=round(trend_score, 4),
                classification=classification,
                explanation=explanation,
                volume_current=window_rec["volume"],
                volume_previous=window_rec["volume_previous"],
                volume_growth_pct=window_rec["volume_growth_pct"],
                engagement_current=round(window_rec["avg_engagement"], 2)
                if has_engagement
                else None,
                engagement_previous=round(window_rec["engagement_previous"], 2)
                if has_engagement
                else None,
                engagement_growth_pct=window_rec["engagement_growth_pct"]
                if has_engagement
                else None,
                velocity=round(velocity, 4),
                burst_score=round(burst_z, 4),
                recency_score=round(recency, 4),
                sentiment_positive_pct=window_rec["sentiment_positive_pct"],
                sentiment_neutral_pct=window_rec["sentiment_neutral_pct"],
                sentiment_negative_pct=window_rec["sentiment_negative_pct"],
            )
            snapshots.append(snap)

        return snapshots
