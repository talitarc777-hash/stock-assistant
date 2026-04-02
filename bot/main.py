import discord
from discord.ext import commands

from config import (
    ALLOWED_CHANNEL_IDS,
    COMMAND_PREFIX,
    DISCORD_BOT_TOKEN,
    WATCHLIST_TICKERS,
)
from stock_api_client import (
    ApiClientError,
    BackendTimeoutError,
    BackendUnavailableError,
    InvalidTickerApiError,
    analyze,
    forecast,
    watchlist,
)

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
        return "• 暫無說明"
    return "\n".join(f"• {text}" for text in items[:limit])


def _format_price(value) -> str:
    """Format numeric fields with graceful fallback."""
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "N/A"


def _friendly_error_message(exc: Exception) -> str:
    """Convert known exceptions into concise Discord-friendly messages."""
    if isinstance(exc, InvalidTickerApiError):
        return "❌ 無效股票代號，請檢查後重試。"
    if isinstance(exc, BackendTimeoutError):
        return "⏳ 後端回應逾時，請稍後再試。"
    if isinstance(exc, BackendUnavailableError):
        return "🔌 後端服務暫時無法連線，請稍後再試。"
    if isinstance(exc, ValueError):
        return "⚠️ API 回傳格式不完整，請稍後再試。"
    if isinstance(exc, ApiClientError):
        return f"⚠️ API 錯誤：{str(exc)}"
    return f"❌ Backend/API error: {repr(exc)}"


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


@bot.command(name="analyze")
async def analyze_cmd(ctx, ticker: str):
    if not is_allowed(ctx):
        return

    try:
        symbol = ticker.upper()
        data = analyze(symbol)
        print("ANALYZE RAW RESPONSE:", data)
        data = _require_dict(data, "analyze response")

        latest_close = _format_price(data.get("latest_close"))
        score_breakdown = _require_dict(data.get("score_breakdown", {}), "score_breakdown")
        score = score_breakdown.get("total_score", "N/A")
        label = data.get("label", "N/A")
        action = data.get("action_summary_zh", data.get("action_summary", "N/A"))
        bullets = data.get("explanation_bullets_zh", data.get("explanation_bullets", []))
        bullets = _require_list(bullets, "explanation_bullets_zh")

        msg = f"""📊 {symbol}

Latest Close: {latest_close}
Score: {score}
Label: {label}
操作摘要: {action}
重點:
{_format_bullets(bullets, limit=3)}
"""
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
        data = forecast(symbol, period="2y")
        print("FORECAST RAW RESPONSE:", data)
        data = _require_dict(data, "forecast response")

        trend = data.get("trend_regime_zh", data.get("trend_regime_en", "N/A"))
        expected_range = _require_dict(data.get("expected_range", {}), "expected_range")
        lower = _format_price(expected_range.get("lower"))
        upper = _format_price(expected_range.get("upper"))
        levels = _require_dict(data.get("levels", {}), "levels")
        support = _format_price(levels.get("support_level"))
        resistance = _format_price(levels.get("resistance_level"))
        confidence = data.get("confidence_score", "N/A")

        msg = f"""🔮 {symbol}

Trend Regime: {trend}
Expected Range: {lower} - {upper}
Confidence: {confidence}/100
Support: {support}
Resistance: {resistance}
"""
    except Exception as exc:
        print("FORECAST ERROR:", repr(exc))
        msg = _friendly_error_message(exc)

    await ctx.send(msg)


@bot.command(name="watchlist")
async def watchlist_cmd(ctx):
    if not is_allowed(ctx):
        return

    try:
        data = watchlist(WATCHLIST_TICKERS, period="5y")
        print("WATCHLIST RAW RESPONSE:", data)
        data = _require_dict(data, "watchlist response")

        ranked = _require_list(data.get("ranked_results", []), "ranked_results")
        failed = _require_list(data.get("failed_tickers", []), "failed_tickers")
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
            ranked_text = "No ranked results returned."

        failed_text = (
            "\n".join(f"• {row.get('ticker', 'N/A')}: {row.get('error', 'Unknown error')}" for row in failed[:3])
            if failed
            else "• None"
        )

        msg = f"""📋 Watchlist Top Ranked
{ranked_text}

Failed:
{failed_text}
"""
    except Exception as exc:
        print("WATCHLIST ERROR:", repr(exc))
        msg = _friendly_error_message(exc)

    await ctx.send(msg)


bot.run(DISCORD_BOT_TOKEN)
