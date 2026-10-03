"""Mathematically rigorous Trend Scoring functions.

Implements the centered 4-signal momentum model with exponential recency modulation:
- Centered logistic normalization: S(0) = 0.50
- 4 signals: Volume Growth, Engagement Growth, Velocity, Burstiness (z-score)
- Recency modulation factor R in (0, 1]
- Final TrendScore = 0.50 + (M_base - 0.50) * R
- Strict classifications: Emerging, Rising, Stable, Declining
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict

from app.nlp.trends.config import TrendConfig


def logistic_normalize(x: float, k: float = 1.0) -> float:
    """Centered logistic normalization mapping (-inf, +inf) -> (0, 1) with S(0) = 0.50.

    - x < 0 maps to (0.0, 0.50) (contraction / deceleration / below baseline)
    - x = 0 maps to exactly 0.50 (neutral steady state)
    - x > 0 maps to (0.50, 1.0) (growth / acceleration / burst)
    """
    try:
        # Clamp to prevent overflow in math.exp
        clamped = max(-20.0, min(20.0, -k * x))
        return 1.0 / (1.0 + math.exp(clamped))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def compute_recency(
    latest_post_time_utc: datetime,
    now_utc: datetime,
    decay_rate: float = 0.05,
) -> float:
    """Calculate recency modulation factor R in (0.0, 1.0] via exponential decay.

    Recency is a freshness modulation factor, NOT an additive growth signal.
    """
    if latest_post_time_utc.tzinfo is None:
        latest_post_time_utc = latest_post_time_utc.replace(tzinfo=timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    elapsed_hours = max(0.0, (now_utc - latest_post_time_utc).total_seconds() / 3600.0)
    return math.exp(-decay_rate * elapsed_hours)


def compute_base_momentum(
    norm_vol: float,
    norm_eng: float,
    norm_vel: float,
    norm_burst: float,
    has_engagement: bool = True,
    config: TrendConfig = TrendConfig(),
) -> float:
    """Combine the 4 centered signals into base momentum M_base.

    - If engagement metrics exist/are mapped: uses approved weights (0.35, 0.25, 0.20, 0.20)
    - If engagement metrics are unavailable in dataset: redistributes weight proportionally
      (0.467, 0, 0.267, 0.266)
    - If engagement is present with value 0: has_engagement=True and S(0)=0.50 is used.
    """
    if has_engagement:
        w_vol = config.weight_volume
        w_eng = config.weight_engagement
        w_vel = config.weight_velocity
        w_burst = config.weight_burstiness
    else:
        # Proportionally redistribute engagement weight (0.25) across remaining signals
        total_non_eng = config.weight_volume + config.weight_velocity + config.weight_burstiness
        if total_non_eng > 0:
            w_vol = config.weight_volume / total_non_eng
            w_eng = 0.0
            w_vel = config.weight_velocity / total_non_eng
            w_burst = config.weight_burstiness / total_non_eng
        else:
            w_vol, w_eng, w_vel, w_burst = 0.333, 0.0, 0.333, 0.334

    momentum = (w_vol * norm_vol) + (w_eng * norm_eng) + (w_vel * norm_vel) + (w_burst * norm_burst)
    return max(0.0, min(1.0, momentum))


def compute_trend_score(
    base_momentum: float,
    recency_factor: float,
) -> float:
    """Modulate base momentum by recency to calculate final TrendScore in [0, 1].

    Formula: TrendScore = 0.50 + (M_base - 0.50) * R
    Mathematical Guarantee:
    If M_base == 0.50 (neutral), TrendScore is ALWAYS 0.50 regardless of recency.
    """
    recency_factor = max(0.0, min(1.0, recency_factor))
    score = 0.50 + (base_momentum - 0.50) * recency_factor
    return max(0.0, min(1.0, score))


def classify_trend(
    trend_score: float,
    volume_current: int,
    volume_previous: int,
    topic_age_windows: int,
    min_posts: int = 3,
    config: TrendConfig = TrendConfig(),
) -> str:
    """Classify trend into emerging, rising, stable, declining.

    Emerging is checked BEFORE Rising.
    Tiny samples (< min_posts) are classified as Stable to prevent spurious trends.
    """
    # Guard against spurious classification on tiny samples
    if volume_current < min_posts:
        return "stable"

    # Emerging check
    is_emerging_candidate = (topic_age_windows < 2) or (volume_previous == 0)
    if trend_score >= config.threshold_emerging and is_emerging_candidate:
        return "emerging"

    # Rising check
    if trend_score >= config.threshold_rising:
        return "rising"

    # Stable check
    if trend_score >= config.threshold_stable:
        return "stable"

    # Declining check
    return "declining"


def generate_explanation(metrics: Dict[str, Any]) -> str:
    """Generate deterministic, statistics-based explanation.

    Burst z-score is strictly described in standard deviations, never as a ratio.
    """
    parts = []

    vg = metrics.get("volume_growth_pct")
    if vg is not None:
        if vg > 15:
            parts.append(f"Post volume increased by {vg:.0f}% compared to the previous period")
        elif vg < -15:
            parts.append(f"Post volume decreased by {abs(vg):.0f}% compared to the previous period")

    eg = metrics.get("engagement_growth_pct")
    if eg is not None:
        if eg > 15:
            parts.append(f"engagement grew by {eg:.0f}%")
        elif eg < -15:
            parts.append(f"engagement dropped by {abs(eg):.0f}%")

    bs = metrics.get("burst_score")
    if bs is not None:
        if bs >= 2.0:
            parts.append(f"activity is {bs:.1f} standard deviations above the historical baseline")
        elif bs <= -2.0:
            parts.append(
                f"activity is {abs(bs):.1f} standard deviations below the historical baseline"
            )

    vel = metrics.get("velocity")
    if vel is not None:
        if vel > 0.5:
            parts.append("growth is accelerating")
        elif vel < -0.5:
            parts.append("growth is decelerating")

    if not parts:
        return "Activity levels and engagement remain consistent with historical norms."

    return ". ".join(parts) + "."
