"""Shared API utilities for validation and JSON-safe serialization."""

from __future__ import annotations

import math
import re
from typing import Any

TICKER_PATTERN = r"^[A-Za-z0-9.\-^=]{1,15}$"
PERIOD_PATTERN = r"^(\d+(d|mo|y)|ytd|max)$"


def to_json_safe(value: Any) -> Any:
    """Convert numpy/pandas scalar values into JSON-safe Python values."""
    if value is None:
        return None
    if isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)
    if hasattr(value, "item"):
        return to_json_safe(value.item())
    return value


def to_json_safe_dict(payload: dict[str, Any]) -> dict[str, Any]:
    """Convert all dict values into JSON-safe values."""
    return {key: to_json_safe(value) for key, value in payload.items()}


def parse_ticker_csv(tickers: str) -> list[str]:
    """Parse and validate comma-separated ticker symbols."""
    parsed = [item.strip().upper() for item in tickers.split(",") if item.strip()]
    if not parsed:
        raise ValueError("At least one ticker is required.")

    invalid = [item for item in parsed if re.fullmatch(TICKER_PATTERN, item) is None]
    if invalid:
        raise ValueError(
            f"Invalid ticker format: {invalid}. "
            "Use alphanumeric symbols with optional . - ^ = characters."
        )
    return parsed
