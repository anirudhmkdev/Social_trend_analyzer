"""Trend detection engine package."""

from app.nlp.trends.aggregator import (
    TemporalAggregator,
    get_utc_window_end,
    get_utc_window_start,
)
from app.nlp.trends.config import TrendConfig
from app.nlp.trends.engine import ComputedTrendSnapshot, TrendEngine
from app.nlp.trends.scoring import (
    classify_trend,
    compute_base_momentum,
    compute_recency,
    compute_trend_score,
    generate_explanation,
    logistic_normalize,
)

__all__ = [
    "ComputedTrendSnapshot",
    "TemporalAggregator",
    "TrendConfig",
    "TrendEngine",
    "classify_trend",
    "compute_base_momentum",
    "compute_recency",
    "compute_trend_score",
    "generate_explanation",
    "get_utc_window_end",
    "get_utc_window_start",
    "logistic_normalize",
]
