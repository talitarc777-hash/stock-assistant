"""Formatting helpers for beginner-friendly Discord bot replies."""

from __future__ import annotations

from typing import Any


def _text(language: str, en: str, zh: str, bilingual: str | None = None) -> str:
    """Pick a short UI label based on the user's language mode."""
    if language == "en":
        return en
    if language == "zh":
        return zh
    return bilingual or f"{en} / {zh}"


def _format_price(value: Any) -> str:
    """Format a numeric price with a safe fallback."""
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "N/A"


def _format_bool(value: bool) -> str:
    """Render a boolean setting in a user-friendly way."""
    return "on" if value else "off"


def _select_language_text(data: dict[str, Any], base_key: str, language: str) -> Any:
    """Select one field variant based on the user's language preference."""
    if language == "en":
        return data.get(f"{base_key}_en", data.get(base_key))
    if language == "bilingual":
        return data.get(f"{base_key}_bilingual", data.get(base_key))
    return data.get(f"{base_key}_zh", data.get(base_key))


def _format_bullets(items: list[str], limit: int = 3, fallback: str = "- No details yet") -> str:
    """Render a short bullet list for Discord."""
    if not items:
        return fallback
    return "\n".join(f"- {item}" for item in items[:limit])


def format_settings_message(user_id: int, settings: dict[str, Any]) -> str:
    """Render current per-user settings clearly and briefly."""
    watchlist = ", ".join(settings.get("default_watchlist", [])) or "system default"
    return (
        "Your settings\n"
        f"- User ID: {user_id}\n"
        f"- Language: {settings.get('language', 'zh')}\n"
        f"- Compact mode: {_format_bool(bool(settings.get('compact_mode', False)))}\n"
        f"- Watchlist: {watchlist}\n"
        "Tip: use `!addticker` or `!removeticker` for quick changes."
    )


def format_help_message(prefix: str) -> str:
    """Render a short, practical help guide."""
    return (
        "Stock bot help\n"
        "Use these commands to check one ticker, your watchlist, or alerts.\n"
        "You can also type simple natural requests like `analyze VOO` or `show my settings`.\n"
        "\n"
        "Main commands\n"
        f"- `{prefix}analyze VOO` check one ticker\n"
        f"- `{prefix}forecast NVDA` view the outlook\n"
        f"- `{prefix}watchlist` rank your watchlist\n"
        f"- `{prefix}alerts` show current alert signals\n"
        "\n"
        "Settings\n"
        f"- `{prefix}settings`\n"
        f"- `{prefix}setlang en|zh|bilingual`\n"
        f"- `{prefix}setcompact on|off`\n"
        f"- `{prefix}setwatchlist VOO,QQQ,AAPL`\n"
        f"- `{prefix}addticker MSFT`\n"
        f"- `{prefix}removeticker QQQ`\n"
        f"- `{prefix}resetsettings`\n"
        "\n"
        "Natural-language examples\n"
        "- `set my language to Chinese`\n"
        "- `turn on compact mode`\n"
        "- `add Tesla to my watchlist`\n"
        "- `show my watchlist`\n"
        "- `what do you think about NVDA`\n"
        "- `what is the outlook for Apple`\n"
        "\n"
        "Quick start\n"
        f"1. `{prefix}setlang bilingual`\n"
        f"2. `{prefix}addticker AMZN`\n"
        f"3. `{prefix}watchlist`"
    )


def format_analyze_message(symbol: str, data: dict[str, Any], settings: dict[str, Any]) -> str:
    """Format analyze response using the user's settings."""
    language = settings.get("language", "zh")
    compact_mode = bool(settings.get("compact_mode", False))

    score_breakdown = data.get("score_breakdown", {})
    latest_close = _format_price(data.get("latest_close"))
    score = score_breakdown.get("total_score", "N/A")
    label = data.get("label", "N/A")
    action = _select_language_text(data, "action_summary", language) or "N/A"
    bullets = _select_language_text(data, "explanation_bullets", language) or []
    if not isinstance(bullets, list):
        bullets = []

    if compact_mode:
        return (
            f"{symbol} snapshot\n"
            f"- Close: {latest_close}\n"
            f"- Score: {score}\n"
            f"- Action: {action}"
        )

    return (
        f"{symbol} analysis\n"
        f"- Close: {latest_close}\n"
        f"- Score: {score}\n"
        f"- Label: {label}\n"
        f"- Action: {action}\n"
        "\n"
        "Why it stands out\n"
        f"{_format_bullets(bullets, limit=3, fallback='- No explanation available yet')}"
    )


def format_forecast_message(symbol: str, data: dict[str, Any], settings: dict[str, Any]) -> str:
    """Format forecast response using the user's settings."""
    language = settings.get("language", "zh")
    compact_mode = bool(settings.get("compact_mode", False))

    if language == "zh":
        trend = data.get("trend_regime_zh", data.get("trend_regime", "N/A"))
    elif language == "bilingual":
        trend = f"{data.get('trend_regime_en', 'N/A')} / {data.get('trend_regime_zh', 'N/A')}"
    else:
        trend = data.get("trend_regime_en", data.get("trend_regime", "N/A"))

    expected_range = data.get("expected_range", {})
    levels = data.get("levels", {})
    lower = _format_price(expected_range.get("lower"))
    upper = _format_price(expected_range.get("upper"))
    support = _format_price(levels.get("support_level"))
    resistance = _format_price(levels.get("resistance_level"))
    confidence = data.get("confidence_score", "N/A")

    title = _text(language, "Forecast", "預測")
    trend_label = _text(language, "Trend", "趨勢")
    range_label = _text(language, "Expected range", "預期區間")
    confidence_label = _text(language, "Confidence", "信心")
    support_label = _text(language, "Support", "支撐")
    resistance_label = _text(language, "Resistance", "阻力")

    if compact_mode:
        return (
            f"{title}: {symbol}\n"
            f"- {trend_label}: {trend}\n"
            f"- {range_label}: {lower} - {upper}\n"
            f"- {confidence_label}: {confidence}/100"
        )

    return (
        f"{title}: {symbol}\n"
        f"- {trend_label}: {trend}\n"
        f"- {range_label}: {lower} - {upper}\n"
        f"- {confidence_label}: {confidence}/100\n"
        f"- {support_label}: {support}\n"
        f"- {resistance_label}: {resistance}"
    )


def format_watchlist_message(
    ranked: list[dict[str, Any]],
    failed: list[dict[str, Any]],
    used_watchlist: list[str],
    settings: dict[str, Any],
) -> str:
    """Format watchlist response using the user's settings."""
    language = settings.get("language", "zh")
    compact_mode = bool(settings.get("compact_mode", False))
    top_rows = ranked[:5]

    if top_rows:
        lines = []
        for index, item in enumerate(top_rows, start=1):
            ticker = item.get("ticker", "N/A")
            score = item.get("score_breakdown", {}).get("total_score", "N/A")
            label = item.get("label", "N/A")
            lines.append(f"{index}. {ticker} | Score: {score} | {label}")
        ranked_text = "\n".join(lines)
    else:
        ranked_text = _text(language, "No ranked results yet.", "暫時未有排名結果。")

    title = _text(language, "Watchlist", "觀察名單")
    using_label = _text(language, "Using", "使用中")
    top_ranked_label = _text(language, "Top ranked", "最高排名")
    failed_label = _text(language, "Skipped", "略過")
    none_label = _text(language, "- None", "- 無")

    if compact_mode:
        return f"{title}\n{ranked_text}"

    failed_text = (
        "\n".join(
            f"- {row.get('ticker', 'N/A')}: {row.get('error', 'Unknown error')}"
            for row in failed[:3]
        )
        if failed
        else none_label
    )
    watchlist_text = ", ".join(used_watchlist) if used_watchlist else "(empty)"
    return (
        f"{title}\n"
        f"- {using_label}: {watchlist_text}\n"
        "\n"
        f"{top_ranked_label}\n"
        f"{ranked_text}\n"
        "\n"
        f"{failed_label}\n"
        f"{failed_text}"
    )


def format_alerts_message(alert_lines: list[str], settings: dict[str, Any]) -> str:
    """Format a Discord alert block for current watchlist alerts."""
    language = settings.get("language", "zh")
    title = _text(language, "Current alerts", "目前提醒")
    no_alerts = _text(language, "No new alerts right now.", "暫時未有新提醒。")
    if not alert_lines:
        return f"{title}\n{no_alerts}"
    return f"{title}\n" + "\n".join(alert_lines)
