import discord
from discord.ext import commands

try:
    from .config import (
        ALLOWED_CHANNEL_IDS,
        COMMAND_PREFIX,
        DISCORD_BOT_TOKEN,
    )
    from .formatter import (
        format_analyze_message,
        format_alerts_message,
        format_forecast_message,
        format_help_message,
        format_settings_message,
        format_watchlist_message,
    )
    from .alert_engine import build_ticker_alerts, format_alert_for_discord
    from .nlp_router import parse_natural_language_message
    from .settings_store import (
        add_user_ticker,
        get_effective_watchlist,
        get_user_settings,
        parse_watchlist_input,
        reset_user_settings,
        remove_user_ticker,
        set_user_compact_mode,
        set_user_language,
        set_user_watchlist,
    )
    from .stock_api_client import (
        ApiClientError,
        BackendTimeoutError,
        BackendUnavailableError,
        InvalidTickerApiError,
        analyze,
        chart_data,
        forecast,
        watchlist,
    )
except ImportError:  # pragma: no cover - script execution fallback
    from config import (
        ALLOWED_CHANNEL_IDS,
        COMMAND_PREFIX,
        DISCORD_BOT_TOKEN,
    )
    from formatter import (
        format_analyze_message,
        format_alerts_message,
        format_forecast_message,
        format_help_message,
        format_settings_message,
        format_watchlist_message,
    )
    from alert_engine import build_ticker_alerts, format_alert_for_discord
    from nlp_router import parse_natural_language_message
    from settings_store import (
        add_user_ticker,
        get_effective_watchlist,
        get_user_settings,
        parse_watchlist_input,
        reset_user_settings,
        remove_user_ticker,
        set_user_compact_mode,
        set_user_language,
        set_user_watchlist,
    )
    from stock_api_client import (
        ApiClientError,
        BackendTimeoutError,
        BackendUnavailableError,
        InvalidTickerApiError,
        analyze,
        chart_data,
        forecast,
        watchlist,
    )

intents = discord.Intents.default()
intents.message_content = True

# Disable discord.py's default help so we can provide a beginner-friendly version.
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)


def is_allowed(ctx) -> bool:
    """Allow command in configured channels only (or all if not configured)."""
    if not ALLOWED_CHANNEL_IDS:
        return True
    return ctx.channel.id in ALLOWED_CHANNEL_IDS


def _friendly_error_message(exc: Exception) -> str:
    """Convert known exceptions into short, friendly chat messages."""
    if isinstance(exc, InvalidTickerApiError):
        return "I couldn't recognise that ticker. Please check it and try again, for example `!analyze VOO`."
    if isinstance(exc, BackendTimeoutError):
        return "The backend is taking a bit too long to reply. Please try again in a moment."
    if isinstance(exc, BackendUnavailableError):
        return "The backend isn't available right now. Please try again a little later."
    if isinstance(exc, ValueError):
        message = str(exc)
        if "Language must be one of" in message:
            return "That language option isn't valid. Use `en`, `zh`, or `bilingual`."
        if "Ticker cannot be empty" in message:
            return "Please enter a ticker. Try something like `!addticker MSFT`."
        if "Watchlist cannot be empty" in message:
            return "Your watchlist is empty. Try `!setwatchlist VOO,QQQ,AAPL`."
        if "Unexpected API shape" in message:
            return "The API reply was missing some expected fields. Please try again later."
        return message
    if isinstance(exc, ApiClientError):
        return f"API error: {str(exc)}"
    return "Something went wrong while talking to the backend. Please try again."


def _require_dict(data, field_name: str) -> dict:
    """Ensure a field is a dictionary for predictable parsing."""
    if isinstance(data, dict):
        return data
    raise ValueError(f"Unexpected API shape: '{field_name}' should be an object.")


def _require_list(data, field_name: str) -> list:
    """Ensure a field is a list for predictable parsing."""
    if isinstance(data, list):
        return data
    raise ValueError(f"Unexpected API shape: '{field_name}' should be a list.")


def _language_label(language: str) -> str:
    """Render a short human-friendly language label."""
    labels = {
        "en": "English",
        "zh": "中文",
        "bilingual": "English + 中文",
    }
    return labels.get(str(language).lower(), str(language))


async def _send_settings(ctx) -> None:
    """Send the current user's saved settings."""
    user_settings = get_user_settings(ctx.author.id)
    print(f"SETTINGS user={ctx.author.id} settings={user_settings}")
    await ctx.send(format_settings_message(ctx.author.id, user_settings))


async def _apply_language_setting(ctx, language: str) -> None:
    """Save language preference and send a friendly confirmation."""
    user_settings = set_user_language(ctx.author.id, language)
    print(f"SETLANG user={ctx.author.id} language={user_settings['language']}")
    await ctx.send(
        f"Done — I'll reply in {_language_label(user_settings['language'])} from now on.\n"
        f"Use `{COMMAND_PREFIX}settings` any time to review your setup."
    )


async def _apply_compact_setting(ctx, compact_mode: bool) -> None:
    """Save compact mode preference and send a friendly confirmation."""
    user_settings = set_user_compact_mode(ctx.author.id, compact_mode)
    print(f"SETCOMPACT user={ctx.author.id} compact_mode={user_settings['compact_mode']}")
    mode_text = "on" if user_settings["compact_mode"] else "off"
    extra = "I'll keep replies shorter." if user_settings["compact_mode"] else "I'll include a bit more detail."
    await ctx.send(
        f"Done — compact mode is now `{mode_text}`.\n"
        f"{extra}"
    )


async def _apply_watchlist_update(ctx, tickers: list[str], action: str) -> None:
    """Add or remove one or more tickers from the user's watchlist."""
    if action == "add":
        updated = get_user_settings(ctx.author.id)
        for ticker in tickers:
            updated = add_user_ticker(ctx.author.id, ticker)
        print(f"ADDTICKER user={ctx.author.id} watchlist={updated['default_watchlist']}")
        added_text = ", ".join(tickers)
        watchlist_text = ", ".join(updated["default_watchlist"])
        await ctx.send(
            f"Added `{added_text}` to your watchlist.\n"
            f"Now using: `{watchlist_text}`"
        )
        return

    updated = get_user_settings(ctx.author.id)
    for ticker in tickers:
        updated = remove_user_ticker(ctx.author.id, ticker)
    print(f"REMOVETICKER user={ctx.author.id} watchlist={updated['default_watchlist']}")
    removed_text = ", ".join(tickers)
    watchlist_text = ", ".join(updated["default_watchlist"])
    await ctx.send(
        f"Removed `{removed_text}` from your watchlist.\n"
        f"Now using: `{watchlist_text}`"
    )


async def _send_analyze(ctx, symbol: str) -> None:
    """Fetch and send an analysis reply for one ticker."""
    user_settings = get_user_settings(ctx.author.id)
    data = analyze(symbol)
    print("ANALYZE RAW RESPONSE:", data)
    data = _require_dict(data, "analyze response")
    _require_dict(data.get("score_breakdown", {}), "score_breakdown")
    await ctx.send(format_analyze_message(symbol, data, user_settings))


async def _send_forecast(ctx, symbol: str) -> None:
    """Fetch and send a forecast reply for one ticker."""
    user_settings = get_user_settings(ctx.author.id)
    data = forecast(symbol, period="2y")
    print("FORECAST RAW RESPONSE:", data)
    data = _require_dict(data, "forecast response")
    _require_dict(data.get("expected_range", {}), "expected_range")
    _require_dict(data.get("levels", {}), "levels")
    await ctx.send(format_forecast_message(symbol, data, user_settings))


async def _send_watchlist(ctx) -> None:
    """Fetch and send ranked watchlist results."""
    user_settings = get_user_settings(ctx.author.id)
    effective_watchlist = get_effective_watchlist(ctx.author.id)
    if not effective_watchlist:
        raise ValueError("Watchlist cannot be empty. Add one with `!setwatchlist VOO,QQQ,AAPL`.")

    data = watchlist(",".join(effective_watchlist), period="5y")
    print("WATCHLIST RAW RESPONSE:", data)
    data = _require_dict(data, "watchlist response")
    ranked = _require_list(data.get("ranked_results", []), "ranked_results")
    failed = _require_list(data.get("failed_tickers", []), "failed_tickers")
    await ctx.send(format_watchlist_message(ranked, failed, effective_watchlist, user_settings))


async def _send_alerts(ctx) -> None:
    """Fetch and send current alert messages for the effective watchlist."""
    user_settings = get_user_settings(ctx.author.id)
    effective_watchlist = get_effective_watchlist(ctx.author.id)
    if not effective_watchlist:
        raise ValueError("Watchlist cannot be empty. Add one with `!setwatchlist VOO,QQQ,AAPL`.")

    watchlist_payload = watchlist(",".join(effective_watchlist), period="5y")
    print("ALERTS WATCHLIST RAW RESPONSE:", watchlist_payload)
    watchlist_payload = _require_dict(watchlist_payload, "watchlist response")
    ranked = _require_list(watchlist_payload.get("ranked_results", []), "ranked_results")
    ranked_map = {str(item.get("ticker", "")).upper(): item for item in ranked}

    alert_lines: list[str] = []
    for ticker in effective_watchlist:
        summary_row = ranked_map.get(ticker, {})
        chart_payload = chart_data(ticker, period="6mo")
        print(f"ALERTS CHART RAW RESPONSE {ticker}:", chart_payload)
        chart_payload = _require_dict(chart_payload, "chart_data response")
        series = _require_list(chart_payload.get("series", []), "series")
        alerts = build_ticker_alerts(ticker=ticker, summary_row=summary_row, series=series)
        alert_lines.extend(
            format_alert_for_discord(
                alert,
                language=str(user_settings.get("language", "zh")),
            )
            for alert in alerts
        )

    await ctx.send(format_alerts_message(alert_lines, user_settings))


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message):
    """Handle explicit commands first, then try rule-based natural-language routing."""
    if message.author.bot:
        return

    if ALLOWED_CHANNEL_IDS and message.channel.id not in ALLOWED_CHANNEL_IDS:
        return

    content = (message.content or "").strip()
    if not content:
        return

    if content.startswith(COMMAND_PREFIX):
        await bot.process_commands(message)
        return

    parsed = parse_natural_language_message(content)
    print(
        "NLP ROUTER:",
        {
            "user_id": getattr(message.author, "id", None),
            "intent": parsed.intent,
            "tickers": parsed.tickers,
            "language": parsed.language,
            "compact_mode": parsed.compact_mode,
            "needs_help_hint": parsed.needs_help_hint,
        },
    )

    if not parsed.intent:
        if parsed.needs_help_hint and parsed.message:
            await message.channel.send(parsed.message)
        return

    ctx = await bot.get_context(message)
    try:
        if parsed.intent == "show_settings":
            await _send_settings(ctx)
        elif parsed.intent == "set_language" and parsed.language:
            await _apply_language_setting(ctx, parsed.language)
        elif parsed.intent == "set_compact" and parsed.compact_mode is not None:
            await _apply_compact_setting(ctx, parsed.compact_mode)
        elif parsed.intent == "add_watchlist" and parsed.tickers:
            await _apply_watchlist_update(ctx, parsed.tickers, action="add")
        elif parsed.intent == "remove_watchlist" and parsed.tickers:
            await _apply_watchlist_update(ctx, parsed.tickers, action="remove")
        elif parsed.intent == "show_watchlist":
            await _send_watchlist(ctx)
        elif parsed.intent == "analyze" and parsed.tickers:
            await _send_analyze(ctx, parsed.tickers[0].upper())
        elif parsed.intent == "forecast" and parsed.tickers:
            await _send_forecast(ctx, parsed.tickers[0].upper())
        elif parsed.needs_help_hint and parsed.message:
            await message.channel.send(parsed.message)
        else:
            await message.channel.send(
                "I'm not sure what you want to do. Try `show my settings`, `analyze VOO`, or `add Tesla to my watchlist`."
            )
    except Exception as exc:
        print("NLP ROUTER ERROR:", repr(exc))
        await message.channel.send(_friendly_error_message(exc))


@bot.event
async def on_command_error(ctx, error):
    """Turn common Discord command errors into friendly chat replies."""
    if not is_allowed(ctx):
        return

    if isinstance(error, commands.CommandNotFound):
        await ctx.send(
            f"I don't know that command yet. Use `{COMMAND_PREFIX}help` to see what's available."
        )
        return

    if isinstance(error, commands.MissingRequiredArgument):
        command_name = ctx.command.qualified_name if ctx.command else "command"
        await ctx.send(
            f"You're missing part of `{command_name}`. Use `{COMMAND_PREFIX}help` for quick examples."
        )
        return

    if isinstance(error, commands.BadArgument):
        await ctx.send(
            f"That input doesn't look right. Use `{COMMAND_PREFIX}help` for examples."
        )
        return

    print("COMMAND ERROR:", repr(error))
    await ctx.send(_friendly_error_message(error))


@bot.command(name="help")
async def help_cmd(ctx):
    if not is_allowed(ctx):
        return
    await ctx.send(format_help_message(COMMAND_PREFIX))


@bot.command(name="settings")
async def settings_cmd(ctx):
    if not is_allowed(ctx):
        return

    await _send_settings(ctx)


@bot.command(name="setlang")
async def setlang_cmd(ctx, language: str):
    if not is_allowed(ctx):
        return

    try:
        await _apply_language_setting(ctx, language)
    except Exception as exc:
        print("SETLANG ERROR:", repr(exc))
        await ctx.send(_friendly_error_message(exc))


@bot.command(name="setcompact")
async def setcompact_cmd(ctx, mode: str):
    if not is_allowed(ctx):
        return

    try:
        normalized = mode.strip().lower()
        if normalized not in {"on", "off"}:
            raise ValueError("Invalid compact mode. Use `!setcompact on` or `!setcompact off`.")
        await _apply_compact_setting(ctx, normalized == "on")
    except Exception as exc:
        print("SETCOMPACT ERROR:", repr(exc))
        await ctx.send(_friendly_error_message(exc))


@bot.command(name="setwatchlist")
async def setwatchlist_cmd(ctx, *, raw_watchlist: str):
    if not is_allowed(ctx):
        return

    try:
        tickers = parse_watchlist_input(raw_watchlist)
        user_settings = set_user_watchlist(ctx.author.id, tickers)
        print(f"SETWATCHLIST user={ctx.author.id} watchlist={user_settings['default_watchlist']}")
        watchlist_text = ", ".join(user_settings["default_watchlist"])
        await ctx.send(
            f"Your watchlist is saved.\n"
            f"Using: `{watchlist_text}`"
        )
    except Exception as exc:
        print("SETWATCHLIST ERROR:", repr(exc))
        await ctx.send(_friendly_error_message(exc))


@bot.command(name="addticker")
async def addticker_cmd(ctx, ticker: str):
    if not is_allowed(ctx):
        return

    try:
        await _apply_watchlist_update(ctx, [ticker.upper()], action="add")
    except Exception as exc:
        print("ADDTICKER ERROR:", repr(exc))
        await ctx.send(_friendly_error_message(exc))


@bot.command(name="removeticker")
async def removeticker_cmd(ctx, ticker: str):
    if not is_allowed(ctx):
        return

    try:
        await _apply_watchlist_update(ctx, [ticker.upper()], action="remove")
    except Exception as exc:
        print("REMOVETICKER ERROR:", repr(exc))
        await ctx.send(_friendly_error_message(exc))


@bot.command(name="resetsettings")
async def resetsettings_cmd(ctx):
    if not is_allowed(ctx):
        return

    user_settings = reset_user_settings(ctx.author.id)
    print(f"RESETSETTINGS user={ctx.author.id}")
    await ctx.send(
        "Your settings are back to the defaults.\n"
        f"{format_settings_message(ctx.author.id, user_settings)}"
    )


@bot.command(name="analyze")
async def analyze_cmd(ctx, ticker: str):
    if not is_allowed(ctx):
        return

    try:
        await _send_analyze(ctx, ticker.upper())
    except Exception as exc:
        print("ANALYZE ERROR:", repr(exc))
        await ctx.send(_friendly_error_message(exc))


@bot.command(name="forecast")
async def forecast_cmd(ctx, ticker: str):
    if not is_allowed(ctx):
        return

    try:
        await _send_forecast(ctx, ticker.upper())
    except Exception as exc:
        print("FORECAST ERROR:", repr(exc))
        await ctx.send(_friendly_error_message(exc))


@bot.command(name="watchlist")
async def watchlist_cmd(ctx):
    if not is_allowed(ctx):
        return

    try:
        await _send_watchlist(ctx)
    except Exception as exc:
        print("WATCHLIST ERROR:", repr(exc))
        await ctx.send(_friendly_error_message(exc))


@bot.command(name="alerts")
async def alerts_cmd(ctx):
    if not is_allowed(ctx):
        return

    try:
        await _send_alerts(ctx)
    except Exception as exc:
        print("ALERTS ERROR:", repr(exc))
        await ctx.send(_friendly_error_message(exc))


bot.run(DISCORD_BOT_TOKEN)
