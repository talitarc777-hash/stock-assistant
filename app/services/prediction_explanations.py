"""Reusable explanation helpers for model predictions and virtual trades."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _safe_float(value: Any) -> float | None:
    """Convert values to float when possible."""
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_technical_state_summary(feature_row: pd.Series) -> str:
    """Summarize the technical state in beginner-friendly plain English."""
    close = _safe_float(feature_row.get("close"))
    sma_20 = _safe_float(feature_row.get("sma_20"))
    sma_50 = _safe_float(feature_row.get("sma_50"))
    sma_200 = _safe_float(feature_row.get("sma_200"))
    rsi_14 = _safe_float(feature_row.get("rsi_14"))
    macd_line = _safe_float(feature_row.get("macd_line"))
    macd_signal = _safe_float(feature_row.get("macd_signal"))
    volatility = _safe_float(feature_row.get("rolling_volatility_20_pct"))

    trend_clause = "Technical state looks mixed."
    if close is not None and sma_50 is not None and sma_200 is not None:
        if close > sma_50 and close > sma_200:
            trend_clause = "Technical state is constructive, with price above the 50-day and 200-day averages."
        elif close < sma_50 and close < sma_200:
            trend_clause = "Technical state is soft, with price below the 50-day and 200-day averages."
        else:
            trend_clause = "Technical state is mixed, with price not fully aligned across the major moving averages."

    momentum_parts: list[str] = []
    if rsi_14 is not None:
        if 50 <= rsi_14 <= 65:
            momentum_parts.append(f"RSI is in a steady zone near {rsi_14:.1f}.")
        elif rsi_14 > 70:
            momentum_parts.append(f"RSI is elevated near {rsi_14:.1f}, so chasing strength may add risk.")
        elif rsi_14 < 40:
            momentum_parts.append(f"RSI is weak near {rsi_14:.1f}.")

    if macd_line is not None and macd_signal is not None:
        if macd_line > macd_signal:
            momentum_parts.append("MACD remains on the bullish side.")
        else:
            momentum_parts.append("MACD remains on the bearish side.")

    if volatility is not None:
        if volatility >= 30:
            momentum_parts.append(f"Volatility is elevated at roughly {volatility:.1f}%.")
        elif volatility <= 15:
            momentum_parts.append(f"Volatility is relatively contained at roughly {volatility:.1f}%.")

    if not momentum_parts:
        return trend_clause
    return f"{trend_clause} {' '.join(momentum_parts)}"


def build_news_sentiment_summary(feature_row: pd.Series) -> str:
    """Summarize the recent news signal in cautious wording."""
    article_count = _safe_float(feature_row.get("article_count"))
    article_count_recent = _safe_float(feature_row.get("article_count_recent_7d"))
    average_sentiment = _safe_float(feature_row.get("average_sentiment"))
    average_sentiment_recent = _safe_float(feature_row.get("average_sentiment_recent_7d"))
    positive_ratio = _safe_float(feature_row.get("positive_article_ratio"))
    negative_ratio = _safe_float(feature_row.get("negative_article_ratio"))
    positive_ratio_recent = _safe_float(feature_row.get("positive_article_ratio_recent_7d"))
    negative_ratio_recent = _safe_float(feature_row.get("negative_article_ratio_recent_7d"))

    using_recent_window = False
    if (article_count is None or article_count <= 0) and article_count_recent is not None and article_count_recent > 0:
        using_recent_window = True
        article_count = article_count_recent
        average_sentiment = average_sentiment_recent if average_sentiment_recent is not None else average_sentiment
        positive_ratio = positive_ratio_recent if positive_ratio_recent is not None else positive_ratio
        negative_ratio = negative_ratio_recent if negative_ratio_recent is not None else negative_ratio

    if article_count is None or article_count <= 0:
        return "No recent matched news was found for this ticker/date."

    if average_sentiment is not None and average_sentiment > 0.15:
        tone = "Recent news tone was mildly positive"
    elif average_sentiment is not None and average_sentiment < -0.15:
        tone = "Recent news tone was mildly negative"
    else:
        tone = "Recent news tone was fairly balanced"

    scope_text = "from same-day matches" if not using_recent_window else "from the recent 7-day window"
    detail_parts = [f"based on {int(article_count)} article(s) {scope_text}"]
    if positive_ratio is not None:
        detail_parts.append(f"positive ratio {positive_ratio:.0%}")
    if negative_ratio is not None:
        detail_parts.append(f"negative ratio {negative_ratio:.0%}")

    return f"{tone}, {'; '.join(detail_parts)}."


def build_benchmark_strength_summary(feature_row: pd.Series) -> str:
    """Summarize benchmark-relative strength versus VOO or the selected benchmark."""
    strength_score = _safe_float(feature_row.get("benchmark_strength_score"))
    excess_1m = _safe_float(feature_row.get("excess_return_1m_pct"))
    excess_3m = _safe_float(feature_row.get("excess_return_3m_pct"))
    excess_6m = _safe_float(feature_row.get("excess_return_6m_pct"))

    if strength_score is None and excess_1m is None and excess_3m is None and excess_6m is None:
        return "Benchmark-relative strength was not available for this row."

    if strength_score is not None and strength_score >= 75:
        lead_text = "Relative strength versus the benchmark looked favorable."
    elif strength_score is not None and strength_score <= 25:
        lead_text = "Relative strength versus the benchmark looked weak."
    else:
        lead_text = "Relative strength versus the benchmark looked mixed."

    details: list[str] = []
    if excess_1m is not None:
        details.append(f"1-month excess return {excess_1m:.2f}%")
    if excess_3m is not None:
        details.append(f"3-month excess return {excess_3m:.2f}%")
    if excess_6m is not None:
        details.append(f"6-month excess return {excess_6m:.2f}%")

    if not details:
        return lead_text
    return f"{lead_text} {'; '.join(details)}."


def build_prediction_explanation(
    feature_row: pd.Series,
    task_type: str,
    predicted_value: float | int,
    confidence_score: float | None,
) -> dict[str, str]:
    """Build a compact explanation payload for one out-of-sample prediction."""
    technical_summary = build_technical_state_summary(feature_row)
    news_summary = build_news_sentiment_summary(feature_row)
    benchmark_summary = build_benchmark_strength_summary(feature_row)

    if task_type == "classification":
        prediction_view = (
            "Model view: the setup leaned constructive."
            if int(predicted_value) == 1
            else "Model view: the setup leaned cautious."
        )
    else:
        predicted_return = float(predicted_value)
        if predicted_return > 0:
            prediction_view = (
                f"Model view: the forward return estimate was mildly positive at about {predicted_return:.2f}%."
            )
        elif predicted_return < 0:
            prediction_view = (
                f"Model view: the forward return estimate was mildly negative at about {predicted_return:.2f}%."
            )
        else:
            prediction_view = "Model view: the forward return estimate was close to flat."

    confidence_text = (
        f"Confidence was around {confidence_score:.0%}."
        if confidence_score is not None
        else "Confidence was not explicitly available for this prediction."
    )

    explanation = " ".join(
        [
            prediction_view,
            confidence_text,
            technical_summary,
            news_summary,
            benchmark_summary,
        ]
    )
    return {
        "technical_state_summary": technical_summary,
        "news_sentiment_summary": news_summary,
        "benchmark_strength_summary": benchmark_summary,
        "explanation": explanation,
    }


def build_trade_action_summary(action: str, trade_reason: str) -> str:
    """Create a practical action summary for simulated trades."""
    if action == "buy":
        return "The simulator opened a position in response to a constructive model signal."
    if trade_reason == "stop_loss":
        return "The simulator exited to limit downside after the stop loss was reached."
    if trade_reason == "take_profit":
        return "The simulator exited after the take-profit level was reached."
    if trade_reason == "model_bearish_signal":
        return "The simulator exited because the model signal turned cautious."
    return "The simulator closed the position based on its active risk rules."


def build_trade_explanation(
    action: str,
    trade_reason: str,
    threshold_summary: str,
    signal_explanation: str | None = None,
) -> str:
    """Combine action, reason, and threshold context into one reusable message."""
    parts = [build_trade_action_summary(action=action, trade_reason=trade_reason)]
    if signal_explanation:
        parts.append(signal_explanation)
    parts.append(threshold_summary)
    return " ".join(part for part in parts if part)
