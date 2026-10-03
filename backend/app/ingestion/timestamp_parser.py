"""Timestamp parsing utilities: parse multiple formats and normalize to UTC."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

# Common datetime format strings to try (in order of specificity)
_DATETIME_FORMATS = [
    # ISO 8601 variants
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%z",
    # Date + time without T
    "%Y-%m-%d %H:%M:%S.%f%z",
    "%Y-%m-%d %H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    # Date only
    "%Y-%m-%d",
    # US formats
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y",
    # Twitter format: "Mon Jul 15 14:30:00 +0000 2026"
    "%a %b %d %H:%M:%S %z %Y",
    # With dots
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y",
]

# Unix timestamp pattern (numeric string)
_UNIX_TIMESTAMP_RE = re.compile(r"^\d{10,13}$")


def parse_timestamp(raw: str) -> Optional[datetime]:
    """
    Parse a timestamp string into a timezone-aware UTC datetime.

    Attempts ISO 8601, Unix epoch, Twitter, and other common formats.
    Returns None if the string cannot be parsed.

    All returned datetimes are UTC-aware.
    """
    raw = raw.strip()
    if not raw:
        return None

    # --- Unix timestamp (seconds or milliseconds) ---
    if _UNIX_TIMESTAMP_RE.match(raw):
        try:
            ts_int = int(raw)
            # Milliseconds if > 13 digits worth
            if ts_int > 1e12:
                ts_int //= 1000
            return datetime.fromtimestamp(ts_int, tz=timezone.utc)
        except (ValueError, OSError):
            pass

    # --- Try standard format strings ---
    for fmt in _DATETIME_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                # Timezone-naive → assume UTC
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except ValueError:
            continue

    # --- pandas fallback for unusual but parseable formats ---
    try:
        import pandas as pd

        dt = pd.to_datetime(raw, utc=True)
        return dt.to_pydatetime().replace(tzinfo=timezone.utc)
    except Exception:
        pass

    return None
