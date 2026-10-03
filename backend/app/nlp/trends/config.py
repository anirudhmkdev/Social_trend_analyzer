"""Trend detection configuration parameters."""

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class TrendConfig:
    # Signal weights (must sum to 1.0)
    weight_volume: float = 0.35
    weight_engagement: float = 0.25
    weight_velocity: float = 0.20
    weight_burstiness: float = 0.20

    # Sensitivity and scaling
    logistic_k: float = 1.0
    burst_logistic_k: float = 0.5
    decay_rate: float = 0.05
    min_baseline: float = 1.0

    # Classification thresholds
    threshold_emerging: float = 0.70
    threshold_rising: float = 0.60
    threshold_stable: float = 0.40

    # Minimum post requirement for trend classification
    min_posts_for_trend: int = 3
    time_window: str = "daily"  # hourly, daily, weekly

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
