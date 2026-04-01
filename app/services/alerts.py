"""Alert generation logic for watchlist scans and notification workflows."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.services.scoring import ScoringInputError, score_from_indicators


class AlertGenerationError(Exception):
    """Raised when alert generation cannot be computed from input data."""


@dataclass(frozen=True)
class TickerScanResult:
    """Single ticker scan output used by scripts and notification adapters."""

    ticker: str
    latest_close: float
    total_score: int
    label: str
    action_summary: str
    alerts: list[str]


def _require_two_rows(df: pd.DataFrame) -> None:
    """Ensure we have enough rows to evaluate crossover-style alerts."""
    if len(df) < 2:
        raise AlertGenerationError("Need at least 2 rows to evaluate crossover alerts.")


def _score_cross_alerts(ticker: str, previous_score: int, latest_score: int) -> list[str]:
    """Create score-threshold alerts."""
    alerts: list[str] = []
    if previous_score < 80 <= latest_score:
        alerts.append(
            f"[{ticker}] Score crossed above 80 ({previous_score} -> {latest_score}). Attractive setup to watch."
        )
    if previous_score >= 45 > latest_score:
        alerts.append(
            f"[{ticker}] Score fell below 45 ({previous_score} -> {latest_score}). Risk has increased."
        )
    return alerts


def _sma200_cross_alerts(ticker: str, previous_row: pd.Series, latest_row: pd.Series) -> list[str]:
    """Create close-vs-SMA200 crossover alerts."""
    alerts: list[str] = []
    if pd.isna(previous_row["sma_200"]) or pd.isna(latest_row["sma_200"]):
        return alerts

    prev_close = float(previous_row["close"])
    prev_sma200 = float(previous_row["sma_200"])
    latest_close = float(latest_row["close"])
    latest_sma200 = float(latest_row["sma_200"])

    if prev_close <= prev_sma200 and latest_close > latest_sma200:
        alerts.append(f"[{ticker}] Close crossed above SMA200. Trend confirmation improved.")
    if prev_close >= prev_sma200 and latest_close < latest_sma200:
        alerts.append(f"[{ticker}] Close crossed below SMA200. Long-term trend weakened.")
    return alerts


def _macd_bullish_change_alert(ticker: str, previous_row: pd.Series, latest_row: pd.Series) -> list[str]:
    """Create MACD bearish-to-bullish state change alert."""
    if any(
        pd.isna(value)
        for value in [
            previous_row["macd_line"],
            previous_row["macd_signal"],
            latest_row["macd_line"],
            latest_row["macd_signal"],
        ]
    ):
        return []

    was_bearish = float(previous_row["macd_line"]) <= float(previous_row["macd_signal"])
    is_bullish = float(latest_row["macd_line"]) > float(latest_row["macd_signal"])

    if was_bearish and is_bullish:
        return [f"[{ticker}] MACD changed from bearish to bullish momentum."]
    return []


def generate_alert_messages(ticker: str, indicators_df: pd.DataFrame) -> list[str]:
    """
    Generate text alerts for one ticker from indicator history.

    Alert rules:
    - Score crosses above 80
    - Score falls below 45
    - Close crosses above SMA200
    - Close crosses below SMA200
    - MACD changes from bearish to bullish
    """
    if indicators_df.empty:
        raise AlertGenerationError("Cannot generate alerts from an empty indicator DataFrame.")

    _require_two_rows(indicators_df)

    latest_row = indicators_df.iloc[-1]
    previous_row = indicators_df.iloc[-2]

    try:
        latest_score = score_from_indicators(indicators_df).total_score
        previous_score = score_from_indicators(indicators_df.iloc[:-1]).total_score
    except ScoringInputError as exc:
        raise AlertGenerationError(str(exc)) from exc

    alerts: list[str] = []
    alerts.extend(_score_cross_alerts(ticker, previous_score, latest_score))
    alerts.extend(_sma200_cross_alerts(ticker, previous_row, latest_row))
    alerts.extend(_macd_bullish_change_alert(ticker, previous_row, latest_row))
    return alerts


def summarize_attractive_and_risky(results: list[TickerScanResult]) -> dict[str, list[str]]:
    """
    Build a compact attractive/risky summary for watchlist reporting.

    - Attractive: score >= 65
    - Risky: score < 50
    """
    attractive = [item.ticker for item in results if item.total_score >= 65]
    risky = [item.ticker for item in results if item.total_score < 50]
    return {
        "attractive": attractive,
        "risky": risky,
    }

