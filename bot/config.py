import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
ALLOWED_CHANNEL_IDS = os.getenv("ALLOWED_CHANNEL_IDS", "")
WATCHLIST_TICKERS = os.getenv("WATCHLIST_TICKERS", "VOO,SPY,QQQ,AAPL,MSFT,NVDA")

if ALLOWED_CHANNEL_IDS:
    ALLOWED_CHANNEL_IDS = [int(x) for x in ALLOWED_CHANNEL_IDS.split(",")]
else:
    ALLOWED_CHANNEL_IDS = []
