import discord
from discord.ext import commands
from config import DISCORD_BOT_TOKEN, COMMAND_PREFIX, ALLOWED_CHANNEL_IDS
from stock_api_client import analyze, forecast, watchlist

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


def is_allowed(ctx):
    if not ALLOWED_CHANNEL_IDS:
        return True
    return ctx.channel.id in ALLOWED_CHANNEL_IDS


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


@bot.command(name="analyze")
async def analyze_cmd(ctx, ticker: str):
    if not is_allowed(ctx):
        return

    try:
        data = analyze(ticker.upper())

        msg = f"""📊 {ticker.upper()} Analysis

Score: {data.get("total_score", "N/A")}

Action:
{data.get("action_summary", "N/A")}
"""
    except Exception as e:
        msg = f"❌ Error: {str(e)}"

    await ctx.send(msg)


@bot.command(name="forecast")
async def forecast_cmd(ctx, ticker: str):
    if not is_allowed(ctx):
        return

    try:
        data = forecast(ticker.upper())

        msg = f"""🔮 {ticker.upper()} Forecast

Trend: {data.get("trend_regime_en", "N/A")}

Range:
{data.get("expected_range_lower", "?")} - {data.get("expected_range_upper", "?")}

Confidence:
{data.get("confidence_score", "N/A")}
"""
    except Exception as e:
        msg = f"❌ Error: {str(e)}"

    await ctx.send(msg)


@bot.command(name="watchlist")
async def watchlist_cmd(ctx):
    if not is_allowed(ctx):
        return

    try:
        data = watchlist()

        lines = []
        for item in data[:5]:
            lines.append(f"{item['ticker']} - {item['score']}")

        msg = "📊 Top Watchlist\n" + "\n".join(lines)

    except Exception as e:
        msg = f"❌ Error: {str(e)}"

    await ctx.send(msg)


bot.run(DISCORD_BOT_TOKEN)