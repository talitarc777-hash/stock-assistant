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


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


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

    user_settings = get_user_settings(ctx.author.id)
    print(f"SETTINGS user={ctx.author.id} settings={user_settings}")
    await ctx.send(format_settings_message(ctx.author.id, user_settings))


@bot.command(name="setlang")
async def setlang_cmd(ctx, language: str):
    if not is_allowed(ctx):
        return

    try:
        user_settings = set_user_language(ctx.author.id, language)
        print(f"SETLANG user={ctx.author.id} language={user_settings['language']}")
        await ctx.send(
            f"Language saved: `{user_settings['language']}`\n"
            f"Use `{COMMAND_PREFIX}settings` any time to review your setup."
        )
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
        user_settings = set_user_compact_mode(ctx.author.id, normalized == "on")
        print(f"SETCOMPACT user={ctx.author.id} compact_mode={user_settings['compact_mode']}")
        await ctx.send(
            f"Compact mode is now `{ 'on' if user_settings['compact_mode'] else 'off' }`.\n"
            f"Use `{COMMAND_PREFIX}settings` any time to review your setup."
        )
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
        user_settings = add_user_ticker(ctx.author.id, ticker)
        print(f"ADDTICKER user={ctx.author.id} watchlist={user_settings['default_watchlist']}")
        watchlist_text = ", ".join(user_settings["default_watchlist"])
        await ctx.send(
            f"Added `{ticker.upper()}` to your watchlist.\n"
            f"Now using: `{watchlist_text}`"
        )
    except Exception as exc:
        print("ADDTICKER ERROR:", repr(exc))
        await ctx.send(_friendly_error_message(exc))


@bot.command(name="removeticker")
async def removeticker_cmd(ctx, ticker: str):
    if not is_allowed(ctx):
        return

    try:
        user_settings = remove_user_ticker(ctx.author.id, ticker)
        print(f"REMOVETICKER user={ctx.author.id} watchlist={user_settings['default_watchlist']}")
        watchlist_text = ", ".join(user_settings["default_watchlist"])
        await ctx.send(
            f"Removed `{ticker.upper()}` from your watchlist.\n"
            f"Now using: `{watchlist_text}`"
        )
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
        symbol = ticker.upper()
        user_settings = get_user_settings(ctx.author.id)
        data = analyze(symbol)
        print("ANALYZE RAW RESPONSE:", data)
        data = _require_dict(data, "analyze response")
        _require_dict(data.get("score_breakdown", {}), "score_breakdown")

        msg = format_analyze_message(symbol, data, user_settings)
    except Exception as exc:
        print("ANALYZE ERROR:", repr(exc))
        msg = _friendly_error_message(exc)

    await ctx.send(msg)


@bot.command(name="forecast")
async def forecast_cmd(ctx, ticker: str):
    if not is_allowed(ctx):
        return

    try:
        symbol = ticker.upper()
        user_settings = get_user_settings(ctx.author.id)
        data = forecast(symbol, period="2y")
        print("FORECAST RAW RESPONSE:", data)
        data = _require_dict(data, "forecast response")
        _require_dict(data.get("expected_range", {}), "expected_range")
        _require_dict(data.get("levels", {}), "levels")

        msg = format_forecast_message(symbol, data, user_settings)
    except Exception as exc:
        print("FORECAST ERROR:", repr(exc))
        msg = _friendly_error_message(exc)

    await ctx.send(msg)


@bot.command(name="watchlist")
async def watchlist_cmd(ctx):
    if not is_allowed(ctx):
        return

    try:
        user_settings = get_user_settings(ctx.author.id)
        effective_watchlist = get_effective_watchlist(ctx.author.id)
        if not effective_watchlist:
            raise ValueError("Watchlist cannot be empty. Add one with `!setwatchlist VOO,QQQ,AAPL`.")

        data = watchlist(",".join(effective_watchlist), period="5y")
        print("WATCHLIST RAW RESPONSE:", data)
        data = _require_dict(data, "watchlist response")

        ranked = _require_list(data.get("ranked_results", []), "ranked_results")
        failed = _require_list(data.get("failed_tickers", []), "failed_tickers")
        msg = format_watchlist_message(ranked, failed, effective_watchlist, user_settings)
    except Exception as exc:
        print("WATCHLIST ERROR:", repr(exc))
        msg = _friendly_error_message(exc)

    await ctx.send(msg)


@bot.command(name="alerts")
async def alerts_cmd(ctx):
    if not is_allowed(ctx):
        return

    try:
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

        msg = format_alerts_message(alert_lines, user_settings)
    except Exception as exc:
        print("ALERTS ERROR:", repr(exc))
        msg = _friendly_error_message(exc)

    await ctx.send(msg)


bot.run(DISCORD_BOT_TOKEN)
