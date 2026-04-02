import discord
from discord.ext import commands

from config import (
    ALLOWED_CHANNEL_IDS,
    COMMAND_PREFIX,
    DISCORD_BOT_TOKEN,
    WATCHLIST_TICKERS,
)
from stock_api_client import analyze, forecast, watchlist

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


def is_allowed(ctx) -> bool:
    """Allow command in configured channels only (or all if not configured)."""
    if not ALLOWED_CHANNEL_IDS:
        return True
    return ctx.channel.id in ALLOWED_CHANNEL_IDS


def _format_bullets(items: list[str], limit: int = 3) -> str:
    """Render a short bullet list for Discord replies."""
    if not items:
        return "• No explanation available"
    return "\n".join(f"• {text}" for text in items[:limit])


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command(name="analyze")
async def analyze_cmd(ctx, ticker: str):
    if not is_allowed(ctx):
        return

    try:
        symbol = ticker.upper()
        data = analyze(symbol)
        print("ANALYZE RAW RESPONSE:", data)

        score = data.get("score_breakdown", {}).get("total_score", "N/A")
        label = data.get("label", "N/A")
        action = data.get("action_summary_bilingual", data.get("action_summary", "N/A"))
        bullets = data.get("explanation_bullets_bilingual", data.get("explanation_bullets", []))

        msg = f"""📊 {symbol} Analysis

Score: {score}
Label: {label}

Action:
{action}

Why:
{_format_bullets(bullets, limit=3)}
"""
    except Exception as exc:
        print("ANALYZE ERROR:", repr(exc))
        msg = f"❌ Backend/API error: {repr(exc)}"

    await ctx.send(msg)


@bot.command(name="forecast")
async def forecast_cmd(ctx, ticker: str):
    if not is_allowed(ctx):
        return

    try:
        symbol = ticker.upper()
        data = forecast(symbol, period="2y")
        print("FORECAST RAW RESPONSE:", data)

        trend = data.get("trend_regime_zh", data.get("trend_regime_en", "N/A"))
        summary = data.get("forecast_summary_bilingual", data.get("forecast_summary_en", "N/A"))
        expected_range = data.get("expected_range", {})
        lower = expected_range.get("lower", "N/A")
        upper = expected_range.get("upper", "N/A")
        support = data.get("levels", {}).get("support_level", "N/A")
        resistance = data.get("levels", {}).get("resistance_level", "N/A")
        confidence = data.get("confidence_score", "N/A")
        bullets = data.get("explanation_bullets", [])

        msg = f"""🔮 {symbol} Forecast

Trend: {trend}
Confidence: {confidence}/100

Expected Range:
{lower} - {upper}

Levels:
Support: {support}
Resistance: {resistance}

Summary:
{summary}

Why:
{_format_bullets(bullets, limit=3)}
"""
    except Exception as exc:
        print("FORECAST ERROR:", repr(exc))
        msg = f"❌ Backend/API error: {repr(exc)}"

    await ctx.send(msg)


@bot.command(name="watchlist")
async def watchlist_cmd(ctx):
    if not is_allowed(ctx):
        return

    try:
        data = watchlist(WATCHLIST_TICKERS, period="5y")
        print("WATCHLIST RAW RESPONSE:", data)

        ranked = data.get("ranked_results", [])
        failed = data.get("failed_tickers", [])
        top_rows = ranked[:5]

        if top_rows:
            lines = []
            for index, item in enumerate(top_rows, start=1):
                ticker = item.get("ticker", "N/A")
                score = item.get("score_breakdown", {}).get("total_score", "N/A")
                label = item.get("label", "N/A")
                action = item.get("action_summary_bilingual", item.get("action_summary", "N/A"))
                lines.append(f"{index}. {ticker} | Score: {score} | {label} | {action}")
            ranked_text = "\n".join(lines)
        else:
            ranked_text = "No ranked results returned."

        failed_text = (
            "\n".join(f"• {row.get('ticker', 'N/A')}: {row.get('error', 'Unknown error')}" for row in failed[:3])
            if failed
            else "• None"
        )

        msg = f"""📋 Watchlist Snapshot

Tickers:
{WATCHLIST_TICKERS}

Top Ranked:
{ranked_text}

Failed:
{failed_text}
"""
    except Exception as exc:
        print("WATCHLIST ERROR:", repr(exc))
        msg = f"❌ Backend/API error: {repr(exc)}"

    await ctx.send(msg)


bot.run(DISCORD_BOT_TOKEN)
