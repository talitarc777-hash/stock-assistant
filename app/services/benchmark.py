"""Benchmark-relative performance analysis utilities."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


class BenchmarkAnalysisError(Exception):
    """Raised when benchmark comparison cannot be computed."""


@dataclass(frozen=True)
class BenchmarkComparison:
    """Structured benchmark-relative comparison output."""

    benchmark: str
    returns: dict[str, float | None]
    benchmark_returns: dict[str, float | None]
    excess_returns: dict[str, float | None]
    benchmark_strength_score: int


_PERIOD_TO_DAYS: dict[str, int] = {
    "1m": 21,
    "3m": 63,
    "6m": 126,
    "12m": 252,
}


def _validate_close_column(df: pd.DataFrame, name: str) -> None:
    """Ensure required close column exists."""
    if "close" not in df.columns:
        raise BenchmarkAnalysisError(f"{name} DataFrame is missing required 'close' column.")


def _period_return_pct(df: pd.DataFrame, trading_days: int) -> float | None:
    """
    Calculate percentage return over a lookback window.

    Returns None if there is not enough data.
    """
    if len(df) <= trading_days:
        return None
    latest_close = float(df.iloc[-1]["close"])
    past_close = float(df.iloc[-(trading_days + 1)]["close"])
    if past_close == 0:
        return None
    return ((latest_close - past_close) / past_close) * 100


def _build_return_map(df: pd.DataFrame) -> dict[str, float | None]:
    """Compute standard period returns for 1m/3m/6m/12m."""
    return {
        period: _period_return_pct(df, trading_days)
        for period, trading_days in _PERIOD_TO_DAYS.items()
    }


def _compute_benchmark_strength_score(excess_returns: dict[str, float | None]) -> int:
    """
    Convert excess returns into a simple 0-100 relative-strength score.

    Scoring per period (1m/3m/6m/12m):
        - Excess return > 0: +25
        - Else: +0
    """
    score = 0
    for value in excess_returns.values():
        if value is not None and value > 0:
            score += 25
    return score


def compare_to_benchmark(
    ticker_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    benchmark_symbol: str = "VOO",
) -> BenchmarkComparison:
    """
    Compare ticker returns to benchmark returns and compute excess strength.

    Args:
        ticker_df: Price history DataFrame with at least `close`.
        benchmark_df: Benchmark history DataFrame with at least `close`.
        benchmark_symbol: Benchmark ticker label (default VOO).
    """
    if ticker_df.empty:
        raise BenchmarkAnalysisError("Ticker data is empty for benchmark comparison.")
    if benchmark_df.empty:
        raise BenchmarkAnalysisError("Benchmark data is empty for benchmark comparison.")

    _validate_close_column(ticker_df, "Ticker")
    _validate_close_column(benchmark_df, "Benchmark")

    ticker_returns = _build_return_map(ticker_df)
    benchmark_returns = _build_return_map(benchmark_df)

    excess_returns: dict[str, float | None] = {}
    for period in _PERIOD_TO_DAYS:
        t_ret = ticker_returns[period]
        b_ret = benchmark_returns[period]
        excess_returns[period] = (t_ret - b_ret) if (t_ret is not None and b_ret is not None) else None

    strength_score = _compute_benchmark_strength_score(excess_returns)

    return BenchmarkComparison(
        benchmark=benchmark_symbol.strip().upper(),
        returns=ticker_returns,
        benchmark_returns=benchmark_returns,
        excess_returns=excess_returns,
        benchmark_strength_score=strength_score,
    )
