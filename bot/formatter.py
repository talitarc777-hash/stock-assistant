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


def _format_percent(value: Any, decimals: int = 1) -> str:
    """Format a percentage value with a safe fallback."""
    try:
        return f"{float(value):.{decimals}f}%"
    except (TypeError, ValueError):
        return "N/A"


def _format_ratio(value: Any, decimals: int = 1) -> str:
    """Format a ratio between 0 and 1 as a percent string."""
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (TypeError, ValueError):
        return "N/A"


def _format_number(value: Any, decimals: int = 2) -> str:
    """Format a general numeric value safely."""
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return "N/A"


def _format_money(value: Any) -> str:
    """Format a money amount in USD with a safe fallback."""
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def _format_bool(value: bool) -> str:
    """Render a boolean setting in a user-friendly way."""
    return "on" if value else "off"


def _safe_text(value: Any, fallback: str = "N/A") -> str:
    """Return a clean string for display."""
    text = str(value).strip() if value is not None else ""
    return text if text else fallback


def _format_signal_value(value: Any) -> str:
    """Format a binary model signal in a readable way."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return _safe_text(value)
    if numeric == 1.0:
        return "Up / 上升"
    if numeric == 0.0:
        return "Down / 下降"
    return _safe_text(value)


def _select_language_text(data: dict[str, Any], base_key: str, language: str) -> Any:
    """Select one field variant based on the user's language preference."""
    if language == "en":
        return data.get(f"{base_key}_en", data.get(base_key))
    if language == "bilingual":
        return data.get(f"{base_key}_bilingual", data.get(base_key))
    return data.get(f"{base_key}_zh", data.get(base_key))


def _format_bullets(items: list[str], limit: int = 3, fallback: str = "- No details yet.") -> str:
    """Render a short bullet list for Discord."""
    if not items:
        return fallback
    return "\n".join(f"- {item}" for item in items[:limit])


def _coerce_list(value: Any) -> list[Any]:
    """Return a list or an empty list so formatters stay predictable."""
    return value if isinstance(value, list) else []


def format_settings_message(user_id: int, settings: dict[str, Any]) -> str:
    """Render current per-user settings clearly and briefly."""
    watchlist = ", ".join(settings.get("default_watchlist", [])) or "system default"
    alert_watchlist = ", ".join(settings.get("alert_watchlist", [])) or "same as watchlist"
    return (
        "Your settings\n"
        f"- User ID: {user_id}\n"
        f"- Language: {settings.get('language', 'zh')}\n"
        f"- Compact mode: {_format_bool(bool(settings.get('compact_mode', False)))}\n"
        f"- Watchlist: {watchlist}\n"
        f"- Alerts: {_format_bool(bool(settings.get('alert_enabled', True)))} "
        f"(low {settings.get('alert_threshold_low', 45)} / high {settings.get('alert_threshold_high', 80)})\n"
        f"- Alert watchlist: {alert_watchlist}\n"
        "Tip: use `!addticker` or `!removeticker` for quick changes."
    )


def format_help_message(prefix: str) -> str:
    """Render a short, practical help guide."""
    return (
        "Stock bot help\n"
        "Use a command or type a simple request in plain language.\n"
        "\n"
        "Main commands\n"
        f"- `{prefix}analyze VOO` check one ticker\n"
        f"- `{prefix}forecast NVDA` view the outlook\n"
        f"- `{prefix}watchlist` rank your watchlist\n"
        f"- `{prefix}alerts` show current alert signals\n"
        f"- `{prefix}modelstatus VOO` show the latest model signal\n"
        f"- `{prefix}modelaccuracy VOO` show model hit rate and metrics\n"
        f"- `{prefix}virtualtrader VOO` show trader summary\n"
        f"- `{prefix}lasttrades VOO` show recent trades\n"
        f"- `{prefix}whytrade VOO` explain the latest trade\n"
        f"- `{prefix}comparetrader VOO` compare the trader with VOO\n"
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
        "- `model status VOO`\n"
        "- `show prediction accuracy for VOO`\n"
        "- `show virtual trader summary`\n"
        "- `show last 5 trades`\n"
        "- `why did the model buy or sell`\n"
        "- `compare virtual trader vs VOO`"
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
        f"{_format_bullets(bullets, limit=3)}"
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

    title = _text(language, "Forecast", "預測", "Forecast / 預測")
    trend_label = _text(language, "Trend regime", "走勢狀態", "Trend regime / 走勢狀態")
    range_label = _text(language, "Expected range", "預期區間", "Expected range / 預期區間")
    confidence_label = _text(language, "Confidence", "信心評分", "Confidence / 信心評分")
    support_label = _text(language, "Support", "支撐位", "Support / 支撐位")
    resistance_label = _text(language, "Resistance", "阻力位", "Resistance / 阻力位")

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
        ranked_text = _text(language, "No ranked results yet.", "暫時未有排名結果", "No ranked results yet / 暫時未有排名結果")

    title = _text(language, "Watchlist", "觀察名單", "Watchlist / 觀察名單")
    using_label = _text(language, "Using", "使用中", "Using / 使用中")
    top_ranked_label = _text(language, "Top ranked", "最高排名", "Top ranked / 最高排名")
    failed_label = _text(language, "Skipped", "略過", "Skipped / 略過")
    none_label = _text(language, "- None", "- 無", "- None / - 無")

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
    title = _text(language, "Current alerts", "目前提示", "Current alerts / 目前提示")
    no_alerts = _text(language, "No new alerts right now.", "目前沒有新提示。", "No new alerts right now / 目前沒有新提示")
    if not alert_lines:
        return f"{title}\n{no_alerts}"
    return f"{title}\n" + "\n".join(alert_lines)


def format_model_status_message(symbol: str, data: dict[str, Any], settings: dict[str, Any]) -> str:
    """Format the latest model prediction into a compact Discord reply."""
    language = settings.get("language", "zh")
    compact_mode = bool(settings.get("compact_mode", False))
    latest = data.get("latest_prediction", {})

    title = _text(language, "Model status", "模型狀態", "Model status / 模型狀態")
    signal_label = _text(language, "Latest signal", "最新訊號", "Latest signal / 最新訊號")
    confidence_label = _text(language, "Confidence", "信心", "Confidence / 信心")
    actual_label = _text(language, "Actual result", "實際結果", "Actual result / 實際結果")
    reason_label = _text(language, "Reason", "原因摘要", "Reason / 原因摘要")

    predicted_value = latest.get("predicted_value")
    signal_text = _safe_text(predicted_value)
    if latest.get("target_name") == "target_5d_updown":
        signal_text = _format_signal_value(predicted_value)

    confidence_text = _format_ratio(latest.get("confidence_score"))
    actual_value = latest.get("actual_future_result")
    actual_text = _safe_text(actual_value)
    if latest.get("task_type") == "classification" and actual_value is not None:
        actual_text = _format_signal_value(actual_value)

    reason = _safe_text(latest.get("explanation"))
    date_text = _safe_text(latest.get("prediction_date"))

    if compact_mode:
        return (
            f"{title}: {symbol}\n"
            f"- {signal_label}: {signal_text}\n"
            f"- {confidence_label}: {confidence_text}\n"
            f"- {actual_label}: {actual_text}"
        )

    return (
        f"{title}: {symbol}\n"
        f"- Date: {date_text}\n"
        f"- {signal_label}: {signal_text}\n"
        f"- {confidence_label}: {confidence_text}\n"
        f"- {actual_label}: {actual_text}\n"
        f"- {reason_label}: {reason}"
    )


def format_model_accuracy_message(symbol: str, data: dict[str, Any], settings: dict[str, Any]) -> str:
    """Format model evaluation metrics for Discord."""
    language = settings.get("language", "zh")
    compact_mode = bool(settings.get("compact_mode", False))
    metrics_summary = data.get("metrics_summary", {})
    metrics = metrics_summary.get("metrics", {})
    latest_rolling_accuracy = data.get("latest_rolling_accuracy")
    task_type = _safe_text(metrics_summary.get("task_type"), "classification")

    title = _text(language, "Prediction accuracy", "預測表現", "Prediction accuracy / 預測表現")
    rolling_label = _text(language, "Rolling hit rate", "滾動命中率", "Rolling hit rate / 滾動命中率")
    latest_label = _text(language, "Latest", "最新", "Latest / 最新")

    if task_type == "classification":
        lines = [
            f"- {rolling_label}: {_format_ratio(latest_rolling_accuracy)}",
            f"- Accuracy: {_format_ratio(metrics.get('accuracy'))}",
            f"- Precision: {_format_ratio(metrics.get('precision'))}",
            f"- Recall: {_format_ratio(metrics.get('recall'))}",
            f"- F1: {_format_number(metrics.get('f1'), 3)}",
        ]
    else:
        lines = [
            f"- {rolling_label}: {_format_ratio(latest_rolling_accuracy)}",
            f"- MAE: {_format_number(metrics.get('mae'))}",
            f"- RMSE: {_format_number(metrics.get('rmse'))}",
            f"- R2: {_format_number(metrics.get('r2'), 3)}",
            f"- Direction accuracy: {_format_ratio(metrics.get('direction_accuracy'))}",
        ]

    history = _coerce_list(data.get("rolling_accuracy"))
    latest_point = history[-1] if history else {}
    latest_line = f"- {latest_label}: {_safe_text(latest_point.get('date'))}"

    if compact_mode:
        return f"{title}: {symbol}\n" + "\n".join(lines[:3])

    return f"{title}: {symbol}\n{latest_line}\n" + "\n".join(lines)


def format_virtual_trader_summary_message(
    symbol: str,
    data: dict[str, Any],
    settings: dict[str, Any],
) -> str:
    """Format the saved virtual trader summary for Discord."""
    language = settings.get("language", "zh")
    compact_mode = bool(settings.get("compact_mode", False))
    summary = data.get("summary", {})

    title = _text(language, "Virtual trader", "模擬交易", "Virtual trader / 模擬交易")
    pnl_label = _text(language, "PnL", "盈虧", "PnL / 盈虧")
    cash_label = _text(language, "Cash", "現金", "Cash / 現金")
    holdings_label = _text(language, "Holdings", "持倉", "Holdings / 持倉")
    trades_label = _text(language, "Trades", "交易次數", "Trades / 交易次數")
    compare_label = _text(language, "Vs VOO", "相對 VOO", "Vs VOO / 相對 VOO")

    cash = _format_money(summary.get("cash"))
    holdings_count = _format_number(summary.get("holdings"), 4)
    realized = _format_money(summary.get("realized_pnl"))
    unrealized = _format_money(summary.get("unrealized_pnl"))
    trade_count = _safe_text(summary.get("trade_count"))
    outperformance = _format_percent(summary.get("outperformance_vs_benchmark_pct_points"))

    if compact_mode:
        return (
            f"{title}: {symbol}\n"
            f"- {pnl_label}: {realized}\n"
            f"- {cash_label}: {cash}\n"
            f"- {holdings_label}: {holdings_count}"
        )

    return (
        f"{title}: {symbol}\n"
        f"- {cash_label}: {cash}\n"
        f"- {holdings_label}: {holdings_count}\n"
        f"- {pnl_label}: {realized} realized, {unrealized} unrealized\n"
        f"- {trades_label}: {trade_count}\n"
        f"- {compare_label}: {outperformance}"
    )


def format_virtual_trader_trades_message(
    symbol: str,
    data: dict[str, Any],
    settings: dict[str, Any],
    limit: int = 5,
) -> str:
    """Format recent virtual trader trades for Discord."""
    language = settings.get("language", "zh")
    compact_mode = bool(settings.get("compact_mode", False))
    trades = _coerce_list(data.get("trade_log"))[-limit:]

    title = _text(language, "Recent trades", "最近交易", "Recent trades / 最近交易")
    none_text = _text(language, "No trades saved yet.", "暫時未有已保存交易。", "No trades saved yet / 暫時未有已保存交易")
    if not trades:
        return f"{title}: {symbol}\n- {none_text}"

    lines = []
    for trade in reversed(trades):
        action = _safe_text(trade.get("action")).upper()
        price = _format_price(trade.get("price"))
        confidence = _format_ratio(trade.get("model_confidence"))
        timestamp = _safe_text(trade.get("timestamp"))
        if compact_mode:
            lines.append(f"- {timestamp[:10]} | {action} | {price}")
        else:
            lines.append(f"- {timestamp[:10]} | {action} | {price} | conf {confidence}")

    return f"{title}: {symbol}\n" + "\n".join(lines)


def format_trade_reason_message(symbol: str, trade: dict[str, Any], settings: dict[str, Any]) -> str:
    """Format the latest trade explanation for Discord."""
    language = settings.get("language", "zh")
    compact_mode = bool(settings.get("compact_mode", False))

    title = _text(language, "Latest trade reason", "最新交易原因", "Latest trade reason / 最新交易原因")
    action_label = _text(language, "Action", "動作", "Action / 動作")
    threshold_label = _text(language, "Thresholds", "觸發門檻", "Thresholds / 觸發門檻")
    reason_label = _text(language, "Reason", "原因", "Reason / 原因")

    action = _safe_text(trade.get("action")).upper()
    summary = _safe_text(trade.get("action_summary"))
    reason = _safe_text(trade.get("explanation"))
    thresholds = _safe_text(trade.get("threshold_summary"))

    if compact_mode:
        return (
            f"{title}: {symbol}\n"
            f"- {action_label}: {action}\n"
            f"- {reason_label}: {summary}"
        )

    return (
        f"{title}: {symbol}\n"
        f"- {action_label}: {action}\n"
        f"- Summary: {summary}\n"
        f"- {threshold_label}: {thresholds}\n"
        f"- {reason_label}: {reason}"
    )


def format_virtual_trader_compare_message(
    symbol: str,
    data: dict[str, Any],
    settings: dict[str, Any],
) -> str:
    """Format the trader-versus-benchmark comparison for Discord."""
    language = settings.get("language", "zh")
    compact_mode = bool(settings.get("compact_mode", False))
    summary = data.get("summary", {})
    benchmark = data.get("benchmark_comparison", {})

    title = _text(language, "Trader vs VOO", "模擬交易對比 VOO", "Trader vs VOO / 模擬交易對比 VOO")
    trader_label = _text(language, "Trader equity", "模擬組合資產", "Trader equity / 模擬組合資產")
    benchmark_label = _text(language, "VOO equity", "VOO 資產", "VOO equity / VOO 資產")
    gap_label = _text(language, "Difference", "差距", "Difference / 差距")

    trader_equity = _format_money(summary.get("final_equity"))
    benchmark_equity = _format_money(benchmark.get("final_equity"))
    gap = _format_percent(summary.get("outperformance_vs_benchmark_pct_points"))

    if compact_mode:
        return (
            f"{title}: {symbol}\n"
            f"- {trader_label}: {trader_equity}\n"
            f"- {benchmark_label}: {benchmark_equity}\n"
            f"- {gap_label}: {gap}"
        )

    return (
        f"{title}: {symbol}\n"
        f"- {trader_label}: {trader_equity}\n"
        f"- {benchmark_label}: {benchmark_equity}\n"
        f"- {gap_label}: {gap}\n"
        f"- Contributions: {_format_money(summary.get('total_contributions'))}"
    )
