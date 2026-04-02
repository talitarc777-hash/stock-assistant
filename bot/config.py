import os
from dotenv import load_dotenv

load_dotenv()


def _parse_csv_env(value: str) -> list[str]:
    """Parse comma/newline/semicolon separated env values into clean tokens."""
    normalized = value.replace("\n", ",").replace(";", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
ALLOWED_CHANNEL_IDS = os.getenv("ALLOWED_CHANNEL_IDS", "")
WATCHLIST_TICKERS = _parse_csv_env(
    os.getenv("WATCHLIST_TICKERS", "VOO,SPY,QQQ,AAPL,MSFT,NVDA")
)
REPLY_LANGUAGE = os.getenv("REPLY_LANGUAGE", "zh").strip().lower()

if REPLY_LANGUAGE not in {"en", "zh", "bilingual"}:
    REPLY_LANGUAGE = "zh"

if ALLOWED_CHANNEL_IDS:
    ALLOWED_CHANNEL_IDS = [int(x) for x in ALLOWED_CHANNEL_IDS.split(",")]
else:
    ALLOWED_CHANNEL_IDS = []
