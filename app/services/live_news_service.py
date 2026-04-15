"""Near-live news sentiment helper service."""

from __future__ import annotations

import logging
from typing import Any

from app.services.news_debug_service import get_latest_news_sentiment

logger = logging.getLogger(__name__)


def get_live_news_snapshot(ticker: str, period: str = "1mo") -> dict[str, Any]:
    """Return latest available news sentiment snapshot for live simulation."""
    payload = get_latest_news_sentiment(ticker=ticker, period=period, sentiment_model="finbert")
    logger.info(
        "Live news snapshot ticker=%s status=%s fetched=%s matched_recent_days=%s",
        payload.get("ticker"),
        payload.get("status"),
        payload.get("debug", {}).get("fetched_article_count", 0),
        payload.get("debug", {}).get("matched_recent_days", 0),
    )
    return payload
