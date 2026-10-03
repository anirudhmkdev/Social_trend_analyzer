"""Temporal aggregation for UTC time windows."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import numpy as np


def get_utc_window_start(dt: datetime, window_type: str = "daily") -> datetime:
    """Align datetime to strictly UTC calendar boundaries."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    utc_dt = dt.astimezone(timezone.utc)
    if window_type == "hourly":
        return datetime(
            utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, 0, 0, tzinfo=timezone.utc
        )
    elif window_type == "weekly":
        # Align to Monday 00:00:00 UTC
        start_of_day = datetime(utc_dt.year, utc_dt.month, utc_dt.day, 0, 0, 0, tzinfo=timezone.utc)
        return start_of_day - timedelta(days=start_of_day.weekday())
    else:
        # Default daily: 00:00:00 UTC
        return datetime(utc_dt.year, utc_dt.month, utc_dt.day, 0, 0, 0, tzinfo=timezone.utc)


def get_utc_window_end(window_start: datetime, window_type: str = "daily") -> datetime:
    """Compute the UTC end boundary of a window."""
    if window_type == "hourly":
        return window_start + timedelta(hours=1)
    elif window_type == "weekly":
        return window_start + timedelta(days=7)
    else:
        return window_start + timedelta(days=1)


class TemporalAggregator:
    """Aggregate posts and sentiments into UTC temporal windows."""

    def __init__(self, time_window: str = "daily"):
        self.time_window = time_window

    def group_posts_by_window(
        self,
        posts_data: List[Dict[str, Any]],
    ) -> Dict[datetime, List[Dict[str, Any]]]:
        """Group posts into UTC windows sorted chronologically."""
        windows: Dict[datetime, List[Dict[str, Any]]] = {}
        for p in posts_data:
            ts: datetime = p["timestamp"]
            w_start = get_utc_window_start(ts, self.time_window)
            if w_start not in windows:
                windows[w_start] = []
            windows[w_start].append(p)
        return dict(sorted(windows.items(), key=lambda kv: kv[0]))

    def compute_window_metrics(
        self,
        posts_in_window: List[Dict[str, Any]],
        has_engagement: bool = True,
    ) -> Dict[str, Any]:
        """Compute metrics for a single window of posts."""
        n = len(posts_in_window)
        if n == 0:
            return {
                "volume": 0,
                "avg_engagement": 0.0,
                "sentiment_positive_pct": 0.0,
                "sentiment_neutral_pct": 0.0,
                "sentiment_negative_pct": 0.0,
                "latest_post_time": None,
            }

        tot_likes = sum(p.get("likes") or 0 for p in posts_in_window)
        tot_comments = sum(p.get("comments") or 0 for p in posts_in_window)
        tot_shares = sum(p.get("shares") or 0 for p in posts_in_window)
        avg_eng = (tot_likes + tot_comments + tot_shares) / float(n) if has_engagement else 0.0

        pos_count = sum(1 for p in posts_in_window if p.get("sentiment") == "positive")
        neu_count = sum(1 for p in posts_in_window if p.get("sentiment") == "neutral")
        neg_count = sum(1 for p in posts_in_window if p.get("sentiment") == "negative")

        latest_time = max(p["timestamp"] for p in posts_in_window)

        return {
            "volume": n,
            "avg_engagement": avg_eng,
            "sentiment_positive_pct": round(pos_count / float(n), 4),
            "sentiment_neutral_pct": round(neu_count / float(n), 4),
            "sentiment_negative_pct": round(neg_count / float(n), 4),
            "latest_post_time": latest_time,
        }

    def compute_trajectory(
        self,
        window_metrics_list: List[Dict[str, Any]],
        min_baseline: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """Compute momentum signals across consecutive windows for a topic.

        Returns list of enriched window records with:
        volume_growth, engagement_growth, velocity, burst_score (z-score).
        """
        enriched: List[Dict[str, Any]] = []
        historical_volumes: List[int] = []

        prev_vol_growth = 0.0

        for i, curr in enumerate(window_metrics_list):
            v_curr = curr["volume"]
            e_curr = curr["avg_engagement"]

            if i == 0:
                v_prev = 0
                e_prev = 0.0
                vol_growth = (v_curr - v_prev) / min_baseline
                eng_growth = 0.0
                velocity = 0.0
                burst_score = 0.0
            else:
                prev_metric = window_metrics_list[i - 1]
                v_prev = prev_metric["volume"]
                e_prev = prev_metric["avg_engagement"]

                vol_growth = (v_curr - v_prev) / max(float(v_prev), min_baseline)
                eng_growth = (e_curr - e_prev) / max(float(e_prev), 1.0)
                velocity = vol_growth - prev_vol_growth

                # Burstiness: z-score against historical baseline
                if historical_volumes:
                    mean_v = float(np.mean(historical_volumes))
                    std_v = float(np.std(historical_volumes))
                    burst_score = (v_curr - mean_v) / max(std_v, 1.0)
                else:
                    burst_score = 0.0

            historical_volumes.append(v_curr)
            prev_vol_growth = vol_growth

            rec = {
                **curr,
                "volume_previous": v_prev,
                "volume_growth": vol_growth,
                "volume_growth_pct": round(vol_growth * 100.0, 2),
                "engagement_previous": e_prev,
                "engagement_growth": eng_growth,
                "engagement_growth_pct": round(eng_growth * 100.0, 2),
                "velocity": velocity,
                "burst_score": burst_score,
                "topic_age_windows": i + 1,
            }
            enriched.append(rec)

        return enriched
