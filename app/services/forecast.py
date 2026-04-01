"""Scenario-based forecast helpers.

This module does NOT predict exact future prices.
It produces short-term and medium-term outlook scenarios using transparent,
indicator-based rules only.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

import pandas as pd


logger = logging.getLogger(__name__)


class ForecastInputError(Exception):
    """Raised when forecast inputs are missing required data."""


@dataclass(frozen=True)
class ForecastResult:
    """Structured scenario-based forecast output."""

    forecast_horizon_5d: str
    forecast_horizon_20d: str
    trend_regime: str
    expected_range_upper: float
    expected_range_lower: float
    confidence_score: int
    support_level: float
    resistance_level: float
    explanation_bullets: list[str]


def _validate_forecast_columns(df: pd.DataFrame) -> None:
    """Validate required columns for scenario-based forecast logic."""
    required_columns = [
        "high",
        "low",
        "close",
        "sma_20",
        "sma_50",
        "sma_200",
        "rsi_14",
        "macd_line",
        "macd_signal",
        "rolling_volatility_20_pct",
    ]
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ForecastInputError(f"Missing required forecast columns: {missing_columns}")


def _calculate_atr_14(df: pd.DataFrame) -> pd.Series:
    """Calculate ATR(14) using standard true range components."""
    previous_close = df["close"].shift(1)
    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - previous_close).abs(),
            (df["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.rolling(window=14, min_periods=14).mean()


def _find_recent_support_resistance(df: pd.DataFrame, lookback: int = 60) -> tuple[float, float]:
    """
    Estimate support/resistance from recent local lows/highs.

    We look for simple local turning points in the recent window. If none are found,
    fall back to the recent rolling min/max.
    """
    recent_df = df.tail(lookback).reset_index(drop=True)
    local_lows: list[float] = []
    local_highs: list[float] = []

    for index in range(1, len(recent_df) - 1):
        current_low = float(recent_df.iloc[index]["low"])
        prev_low = float(recent_df.iloc[index - 1]["low"])
        next_low = float(recent_df.iloc[index + 1]["low"])
        if current_low <= prev_low and current_low <= next_low:
            local_lows.append(current_low)

        current_high = float(recent_df.iloc[index]["high"])
        prev_high = float(recent_df.iloc[index - 1]["high"])
        next_high = float(recent_df.iloc[index + 1]["high"])
        if current_high >= prev_high and current_high >= next_high:
            local_highs.append(current_high)

    support_level = local_lows[-1] if local_lows else float(recent_df["low"].min())
    resistance_level = local_highs[-1] if local_highs else float(recent_df["high"].max())
    return support_level, resistance_level


def _build_outlook_text(trend_regime: str, horizon_days: int, confidence_score: int) -> str:
    """Build simple, readable scenario text for a forecast horizon."""
    if trend_regime == "bullish":
        if horizon_days == 5:
            return (
                "Short-term outlook remains constructive if price stays above nearby support."
            )
        return (
            "Medium-term outlook stays constructive while the broader uptrend and momentum hold."
        )
    if trend_regime == "bearish":
        if horizon_days == 5:
            return "Short-term outlook remains cautious unless momentum improves."
        return "Medium-term outlook remains weak unless trend structure recovers."
    if confidence_score >= 60:
        return "Outlook is mixed but stable, with range-bound movement more likely than breakout."
    return "Outlook is uncertain, with sideways movement and quick reversals both possible."


def _clamp_confidence_score(raw_score: int) -> int:
    """Clamp confidence score into the requested 0-100 range."""
    return max(0, min(100, raw_score))


def build_scenario_forecast(df: pd.DataFrame) -> ForecastResult:
    """
    Build a scenario-based 5d/20d outlook.

    This is a scenario-based forecast, not a guaranteed prediction.
    It does not predict exact prices.
    """
    if df.empty:
        raise ForecastInputError("Cannot build forecast from empty data.")

    _validate_forecast_columns(df)

    working_df = df.copy()
    working_df["atr_14"] = _calculate_atr_14(working_df)
    latest_row = working_df.iloc[-1]

    current_close = float(latest_row["close"])
    sma_20 = float(latest_row["sma_20"]) if pd.notna(latest_row["sma_20"]) else current_close
    sma_50 = float(latest_row["sma_50"]) if pd.notna(latest_row["sma_50"]) else current_close
    sma_200 = float(latest_row["sma_200"]) if pd.notna(latest_row["sma_200"]) else current_close
    rsi_14 = float(latest_row["rsi_14"]) if pd.notna(latest_row["rsi_14"]) else 50.0
    macd_line = float(latest_row["macd_line"]) if pd.notna(latest_row["macd_line"]) else 0.0
    macd_signal = float(latest_row["macd_signal"]) if pd.notna(latest_row["macd_signal"]) else 0.0
    rolling_volatility = (
        float(latest_row["rolling_volatility_20_pct"])
        if pd.notna(latest_row["rolling_volatility_20_pct"])
        else 25.0
    )

    momentum_positive = macd_line > macd_signal and rsi_14 >= 50
    momentum_weak = macd_line < macd_signal and rsi_14 < 45

    if current_close > sma_50 and current_close > sma_200 and momentum_positive:
        trend_regime = "bullish"
    elif current_close < sma_50 and current_close < sma_200 and momentum_weak:
        trend_regime = "bearish"
    else:
        trend_regime = "neutral"

    atr_14 = float(latest_row["atr_14"]) if pd.notna(latest_row["atr_14"]) else None
    recent_range = float((working_df["high"] - working_df["low"]).tail(14).mean())
    range_band = atr_14 if atr_14 is not None else recent_range

    if trend_regime == "bullish":
        expected_range_upper = current_close + (range_band * 1.25)
        expected_range_lower = current_close - (range_band * 0.75)
    elif trend_regime == "bearish":
        expected_range_upper = current_close + (range_band * 0.75)
        expected_range_lower = current_close - (range_band * 1.25)
    else:
        expected_range_upper = current_close + range_band
        expected_range_lower = current_close - range_band

    support_level, resistance_level = _find_recent_support_resistance(working_df)

    confidence_score = 50
    explanation_bullets: list[str] = [
        "This is a scenario-based forecast, not a guaranteed prediction.",
    ]

    if trend_regime == "bullish":
        confidence_score += 20
        explanation_bullets.append(
            "Price is above SMA50 and SMA200, which keeps the broader trend constructive."
        )
    elif trend_regime == "bearish":
        confidence_score -= 15
        explanation_bullets.append(
            "Price is below SMA50 and SMA200, which points to a weaker trend regime."
        )
    else:
        explanation_bullets.append(
            "Price is between major moving average signals, so the trend regime is mixed."
        )

    if sma_20 > sma_50:
        confidence_score += 10
        explanation_bullets.append("SMA20 is above SMA50, which supports short-term trend follow-through.")
    else:
        confidence_score -= 5
        explanation_bullets.append("SMA20 is not above SMA50, so short-term trend support is limited.")

    if macd_line > macd_signal:
        confidence_score += 10
        explanation_bullets.append("MACD remains above its signal line, which supports positive momentum.")
    else:
        confidence_score -= 10
        explanation_bullets.append("MACD is below its signal line, which keeps momentum softer.")

    if 45 <= rsi_14 <= 65:
        confidence_score += 10
        explanation_bullets.append("RSI is in a balanced zone, which supports a steadier outlook.")
    elif rsi_14 > 75 or rsi_14 < 30:
        confidence_score -= 10
        explanation_bullets.append("RSI is in an extreme zone, so short-term swings may be less stable.")

    if rolling_volatility > 35:
        confidence_score -= 10
        explanation_bullets.append("Rolling volatility is elevated, so the expected range is wider.")
    else:
        confidence_score += 5
        explanation_bullets.append("Rolling volatility is moderate, which improves scenario confidence.")

    explanation_bullets.append(
        f"Support is estimated near {support_level:.2f} and resistance near {resistance_level:.2f}."
    )
    explanation_bullets.append(
        f"Expected range is centered around recent ATR/range behaviour, roughly {expected_range_lower:.2f} to {expected_range_upper:.2f}."
    )

    confidence_score = _clamp_confidence_score(confidence_score)

    logger.info(
        "Built scenario forecast: trend_regime=%s confidence_score=%d",
        trend_regime,
        confidence_score,
    )

    return ForecastResult(
        forecast_horizon_5d=_build_outlook_text(trend_regime, horizon_days=5, confidence_score=confidence_score),
        forecast_horizon_20d=_build_outlook_text(trend_regime, horizon_days=20, confidence_score=confidence_score),
        trend_regime=trend_regime,
        expected_range_upper=float(expected_range_upper),
        expected_range_lower=float(expected_range_lower),
        confidence_score=confidence_score,
        support_level=float(support_level),
        resistance_level=float(resistance_level),
        explanation_bullets=explanation_bullets,
    )

