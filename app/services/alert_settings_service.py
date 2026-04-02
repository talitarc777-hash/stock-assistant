"""Shared alert settings and user-specific alert scan helpers."""

from __future__ import annotations

from app.models.user_profile import (
    UserAlertEventResponse,
    UserAlertScanResponse,
    UserAlertSettingsUpdateRequest,
)
from app.services.indicators import add_technical_indicators
from app.services.market_data import get_price_history
from app.services.scoring import score_from_indicators
from app.services.user_profile_service import get_user_profile_store
from app.services.watchlist_service import get_user_watchlist


def get_user_alert_settings(user_id: str) -> tuple[dict, bool]:
    """Return alert settings and whether alert watchlist falls back to the main watchlist."""
    store = get_user_profile_store()
    profile = store.get_or_create_profile(user_id=user_id)
    fallback_watchlist, _, _ = get_user_watchlist(user_id=user_id)
    using_watchlist_fallback = not bool(profile.alert_watchlist)
    return {
        "user_id": profile.user_id,
        "alert_enabled": profile.alert_enabled,
        "alert_threshold_high": profile.alert_threshold_high,
        "alert_threshold_low": profile.alert_threshold_low,
        "alert_watchlist": profile.alert_watchlist or fallback_watchlist,
        "preferred_delivery_source": profile.preferred_delivery_source,
    }, using_watchlist_fallback


def update_user_alert_settings(request: UserAlertSettingsUpdateRequest):
    """Persist alert preferences into the shared user profile store."""
    return get_user_profile_store().update_alert_settings(request)


def _to_float_or_none(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def scan_user_alerts(user_id: str) -> UserAlertScanResponse:
    """Generate user-specific alerts from the shared alert preferences."""
    store = get_user_profile_store()
    profile = store.get_or_create_profile(user_id=user_id)
    watchlist = profile.alert_watchlist or (profile.default_watchlist or store.default_watchlist)
    if not profile.alert_enabled:
        return UserAlertScanResponse(
            user_id=profile.user_id,
            alert_enabled=False,
            watchlist=watchlist,
            alerts=[],
            suppressed_count=0,
        )

    alerts: list[UserAlertEventResponse] = []
    suppressed_count = 0

    for ticker in watchlist:
        indicators_df = add_technical_indicators(get_price_history(ticker=ticker, period="1y"))
        latest = indicators_df.iloc[-1]
        previous = indicators_df.iloc[-2] if len(indicators_df) >= 2 else latest
        score = score_from_indicators(indicators_df)

        latest_close = float(latest["close"])
        previous_close = float(previous["close"])
        latest_sma200 = _to_float_or_none(latest["sma_200"])
        previous_sma200 = _to_float_or_none(previous["sma_200"])
        prev_macd = _to_float_or_none(previous["macd_line"])
        prev_signal = _to_float_or_none(previous["macd_signal"])
        latest_macd = _to_float_or_none(latest["macd_line"])
        latest_signal = _to_float_or_none(latest["macd_signal"])

        candidate_messages: list[tuple[str, str, str, str, str]] = []

        if score.total_score >= profile.alert_threshold_high:
            candidate_messages.append(
                (
                    "score_above_threshold",
                    "high",
                    f"{ticker}: score reached {score.total_score}, above your high alert threshold.",
                    f"{ticker}: 評分升至 {score.total_score}，高於你的高位提示門檻。",
                    str(score.total_score),
                )
            )
        if score.total_score <= profile.alert_threshold_low:
            candidate_messages.append(
                (
                    "score_below_threshold",
                    "high",
                    f"{ticker}: score fell to {score.total_score}, below your low alert threshold.",
                    f"{ticker}: 評分跌至 {score.total_score}，低於你的低位提示門檻。",
                    str(score.total_score),
                )
            )

        if None not in (latest_sma200, previous_sma200):
            if previous_close <= previous_sma200 and latest_close > latest_sma200:
                candidate_messages.append(
                    (
                        "close_cross_above_sma200",
                        "medium",
                        f"{ticker}: close moved back above SMA200.",
                        f"{ticker}: 收市價重新升穿 SMA200。",
                        f"{latest_close:.2f}>{latest_sma200:.2f}",
                    )
                )
            if previous_close >= previous_sma200 and latest_close < latest_sma200:
                candidate_messages.append(
                    (
                        "close_cross_below_sma200",
                        "medium",
                        f"{ticker}: close slipped below SMA200.",
                        f"{ticker}: 收市價跌穿 SMA200。",
                        f"{latest_close:.2f}<{latest_sma200:.2f}",
                    )
                )

        if None not in (prev_macd, prev_signal, latest_macd, latest_signal):
            if prev_macd <= prev_signal and latest_macd > latest_signal:
                candidate_messages.append(
                    (
                        "macd_bullish_change",
                        "medium",
                        f"{ticker}: MACD turned bullish.",
                        f"{ticker}: MACD 轉為偏強。",
                        f"{latest_macd:.4f}>{latest_signal:.4f}",
                    )
                )
            elif prev_macd >= prev_signal and latest_macd < latest_signal:
                candidate_messages.append(
                    (
                        "macd_bearish_change",
                        "medium",
                        f"{ticker}: MACD turned bearish.",
                        f"{ticker}: MACD 轉為偏弱。",
                        f"{latest_macd:.4f}<{latest_signal:.4f}",
                    )
                )

        for rule, severity, message_en, message_zh, state_key in candidate_messages:
            if store.should_send_alert(profile.user_id, ticker, rule, state_key):
                alerts.append(
                    UserAlertEventResponse(
                        ticker=ticker,
                        rule=rule,
                        severity=severity,
                        message_en=message_en,
                        message_zh=message_zh,
                        suppressed_duplicate=False,
                    )
                )
            else:
                suppressed_count += 1

    return UserAlertScanResponse(
        user_id=profile.user_id,
        alert_enabled=profile.alert_enabled,
        watchlist=watchlist,
        alerts=alerts,
        suppressed_count=suppressed_count,
    )


def scan_all_enabled_user_alerts() -> list[UserAlertScanResponse]:
    """Scan alerts for every user who currently has alerts enabled."""
    store = get_user_profile_store()
    responses: list[UserAlertScanResponse] = []
    for profile in store.list_profiles_with_alerts_enabled():
        responses.append(scan_user_alerts(profile.user_id))
    return responses
