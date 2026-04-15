"""Stock universe management helpers for broader U.S. coverage.

This keeps universe selection modular and beginner-friendly:
- default curated list (fast)
- optional file-based custom universe
- optional capped universe expansion from external sources later
"""

from __future__ import annotations

from pathlib import Path

from app.core.settings import get_settings

DEFAULT_US_UNIVERSE = [
    "VOO",
    "SPY",
    "QQQ",
    "DIA",
    "IWM",
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "BRK-B",
    "JPM",
    "XOM",
]


def _normalize_tickers(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in values:
        symbol = str(item).strip().upper()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        result.append(symbol)
    return result


def load_universe_from_file(path: str | Path) -> list[str]:
    """Load ticker universe from a simple text file (one ticker per line)."""
    target = Path(path)
    if not target.exists():
        return []
    lines = target.read_text(encoding="utf-8").splitlines()
    values: list[str] = []
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        values.append(text)
    return _normalize_tickers(values)


def get_us_universe(limit: int = 500) -> list[str]:
    """Return a capped U.S. universe list for model/simulation jobs."""
    settings_values = _normalize_tickers(get_settings().default_watchlist)
    file_values = load_universe_from_file("config/universe_tickers.txt")
    merged = _normalize_tickers(DEFAULT_US_UNIVERSE + settings_values + file_values)
    return merged[: max(1, int(limit))]
