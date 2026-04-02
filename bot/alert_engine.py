"""Reusable alert detection + Discord message formatting helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AlertEvent:
    """One normalized alert event suitable for logging or Discord posting."""

    ticker: str
    rule: str
    severity: str
    message_en: str
    message_zh: str


def _to_float(value: Any) -> float | None:
    """Convert unknown numeric input to float, returning None when not possible."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def detect_score_alerts(ticker: str, summary_row: dict[str, Any]) -> list[AlertEvent]:
    """Detect score threshold alerts from /watchlist-analyze row."""
    score = summary_row.get("score_breakdown", {}).get("total_score")
    label = str(summary_row.get("label", "N/A"))
    score_float = _to_float(score)
    if score_float is None:
        return []

    alerts: list[AlertEvent] = []
    if score_float > 80:
        alerts.append(
            AlertEvent(
                ticker=ticker,
                rule="score_above_80",
                severity="high",
                message_en=f"{ticker}: score is {int(score_float)} (>80), label: {label}.",
                message_zh=f"{ticker}: 評分為 {int(score_float)}（高於 80），標籤：{label}。",
            )
        )
    if score_float < 45:
        alerts.append(
            AlertEvent(
                ticker=ticker,
                rule="score_below_45",
                severity="high",
                message_en=f"{ticker}: score is {int(score_float)} (<45), label: {label}.",
                message_zh=f"{ticker}: 評分為 {int(score_float)}（低於 45），標籤：{label}。",
            )
        )
    return alerts


def detect_price_and_macd_alerts(ticker: str, series: list[dict[str, Any]]) -> list[AlertEvent]:
    """Detect SMA200 crossing and MACD signal-line change from chart series."""
    if len(series) < 2:
        return []

    previous = series[-2]
    latest = series[-1]

    prev_close = _to_float(previous.get("close"))
    prev_sma200 = _to_float(previous.get("sma_200"))
    latest_close = _to_float(latest.get("close"))
    latest_sma200 = _to_float(latest.get("sma_200"))

    prev_macd = _to_float(previous.get("macd_line"))
    prev_signal = _to_float(previous.get("macd_signal"))
    latest_macd = _to_float(latest.get("macd_line"))
    latest_signal = _to_float(latest.get("macd_signal"))

    alerts: list[AlertEvent] = []

    if None not in (prev_close, prev_sma200, latest_close, latest_sma200):
        if prev_close <= prev_sma200 and latest_close > latest_sma200:
            alerts.append(
                AlertEvent(
                    ticker=ticker,
                    rule="close_cross_above_sma200",
                    severity="medium",
                    message_en=(
                        f"{ticker}: close crossed above SMA200 "
                        f"({latest_close:.2f} > {latest_sma200:.2f})."
                    ),
                    message_zh=(
                        f"{ticker}: 收市價升穿 SMA200 "
                        f"（{latest_close:.2f} > {latest_sma200:.2f}）。"
                    ),
                )
            )
        if prev_close >= prev_sma200 and latest_close < latest_sma200:
            alerts.append(
                AlertEvent(
                    ticker=ticker,
                    rule="close_cross_below_sma200",
                    severity="medium",
                    message_en=(
                        f"{ticker}: close crossed below SMA200 "
                        f"({latest_close:.2f} < {latest_sma200:.2f})."
                    ),
                    message_zh=(
                        f"{ticker}: 收市價跌穿 SMA200 "
                        f"（{latest_close:.2f} < {latest_sma200:.2f}）。"
                    ),
                )
            )

    if None not in (prev_macd, prev_signal, latest_macd, latest_signal):
        if prev_macd <= prev_signal and latest_macd > latest_signal:
            alerts.append(
                AlertEvent(
                    ticker=ticker,
                    rule="macd_bearish_to_bullish",
                    severity="medium",
                    message_en=f"{ticker}: MACD changed from bearish to bullish.",
                    message_zh=f"{ticker}: MACD 由偏弱轉為偏強。",
                )
            )
        elif prev_macd >= prev_signal and latest_macd < latest_signal:
            alerts.append(
                AlertEvent(
                    ticker=ticker,
                    rule="macd_bullish_to_bearish",
                    severity="medium",
                    message_en=f"{ticker}: MACD changed from bullish to bearish.",
                    message_zh=f"{ticker}: MACD 由偏強轉為偏弱。",
                )
            )

    return alerts


def build_ticker_alerts(
    ticker: str,
    summary_row: dict[str, Any],
    series: list[dict[str, Any]],
) -> list[AlertEvent]:
    """Build all required alert types for one ticker."""
    alerts: list[AlertEvent] = []
    alerts.extend(detect_score_alerts(ticker=ticker, summary_row=summary_row))
    alerts.extend(detect_price_and_macd_alerts(ticker=ticker, series=series))
    return alerts


def format_alert_for_discord(alert: AlertEvent, language: str = "zh") -> str:
    """Render one alert as a compact Discord-friendly line."""
    icon = "🚨" if alert.severity == "high" else "⚠️"
    if language == "en":
        message = alert.message_en
    elif language == "bilingual":
        message = f"{alert.message_en} / {alert.message_zh}"
    else:
        message = alert.message_zh
    return f"{icon} {message}"


def format_alert_batch_for_discord(
    alerts: list[AlertEvent],
    title: str,
    language: str = "zh",
) -> str:
    """Render a full Discord message block for a group of alerts."""
    if not alerts:
        no_alerts = "No new alerts." if language == "en" else "目前沒有新的提示。"
        if language == "bilingual":
            no_alerts = "No new alerts. / 目前沒有新的提示。"
        return f"{title}\n{no_alerts}"

    lines = [title]
    lines.extend(format_alert_for_discord(alert, language=language) for alert in alerts)
    return "\n".join(lines)
