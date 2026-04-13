"""Debug helpers for news ingestion and sentiment pipeline visibility."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from app.services.market_data import get_price_history
from app.services.news_sentiment import (
    _aggregate_daily_features,
    _build_scorer,
    _score_articles,
)
from app.services.news_service import YahooFinanceNewsProvider, articles_to_frame

logger = logging.getLogger(__name__)


def build_news_sentiment_debug(
    ticker: str,
    date: str | None = None,
    period: str = "6mo",
    sentiment_model: str = "finbert",
) -> dict[str, Any]:
    """Return end-to-end debug details for news sentiment processing."""
    symbol = str(ticker).strip().upper()
    if not symbol:
        raise ValueError("ticker is required.")

    provider = YahooFinanceNewsProvider()
    scorer = _build_scorer(sentiment_model=sentiment_model, fallback_to_lexicon=True)

    price_df = get_price_history(symbol, period=period)
    date_index = pd.to_datetime(price_df["date"], errors="coerce")
    filter_date = pd.to_datetime(date, errors="coerce") if date else None
    if date and pd.isna(filter_date):
        raise ValueError("date must use YYYY-MM-DD format.")

    articles = provider.fetch_article_metadata(ticker=symbol, company_name=None, limit=120)
    article_df = articles_to_frame(articles)
    scored_df = _score_articles(article_df=article_df, scorer=scorer) if not article_df.empty else article_df.copy()
    features_df = _aggregate_daily_features(scored_article_df=scored_df, date_index=date_index, mapped_ticker=symbol)

    if filter_date is not None:
        day_df = features_df[pd.to_datetime(features_df["date"], errors="coerce") == filter_date]
    else:
        day_df = features_df.tail(1)

    day_payload = day_df.to_dict(orient="records")[0] if not day_df.empty else {}
    recent_headlines = (
        scored_df.sort_values("article_date", ascending=False)["title"].head(5).tolist()
        if not scored_df.empty
        else []
    )

    matched_exact_days = int((features_df["article_count"] > 0).sum()) if not features_df.empty else 0
    matched_recent_days = (
        int((features_df["article_count_recent_7d"] > 0).sum())
        if not features_df.empty and "article_count_recent_7d" in features_df.columns
        else 0
    )

    logger.info(
        "News debug ticker=%s requested_date=%s fetched=%d usable=%d matched_exact_days=%d matched_recent_days=%d",
        symbol,
        date or "",
        len(articles),
        len(scored_df),
        matched_exact_days,
        matched_recent_days,
    )

    return {
        "ticker": symbol,
        "requested_date": date,
        "period": period,
        "sentiment_model": sentiment_model,
        "fetched_article_count": len(articles),
        "usable_article_count": int(len(scored_df)),
        "matched_exact_days": matched_exact_days,
        "matched_recent_days": matched_recent_days,
        "latest_feature_row": day_payload,
        "recent_headlines": recent_headlines,
    }


def get_latest_news_sentiment(
    ticker: str,
    period: str = "6mo",
    sentiment_model: str = "finbert",
) -> dict[str, Any]:
    """Return latest news sentiment snapshot for UI display."""
    payload = build_news_sentiment_debug(
        ticker=ticker,
        date=None,
        period=period,
        sentiment_model=sentiment_model,
    )
    latest = payload.get("latest_feature_row", {}) or {}
    exact_count = int(latest.get("article_count", 0) or 0)
    recent_count = int(latest.get("article_count_recent_7d", 0) or 0)

    if exact_count > 0 or recent_count > 0:
        status = "ok"
        message_en = "Recent matched news features are available."
        message_zh = "\u5df2\u627e\u5230\u53ef\u5339\u914d\u7684\u8fd1\u671f\u65b0\u805e\u7279\u5fb5\u3002"
    elif payload.get("fetched_article_count", 0) <= 0:
        status = "no_news"
        message_en = "No recent matched news was found for this ticker/date."
        message_zh = "\u6b64\u80a1\u7968\u65bc\u8a72\u65e5\u671f\u672a\u627e\u5230\u53ef\u5339\u914d\u7684\u8fd1\u671f\u65b0\u805e\u3002"
    else:
        status = "no_match"
        message_en = "Articles were fetched but did not match this trading-date window."
        message_zh = "\u5df2\u6293\u53d6\u65b0\u805e\uff0c\u4f46\u672a\u80fd\u5c0d\u61c9\u5230\u9019\u500b\u4ea4\u6613\u65e5\u671f\u8996\u7a97\u3002"

    return {
        "ticker": payload["ticker"],
        "period": payload["period"],
        "status": status,
        "message_en": message_en,
        "message_zh": message_zh,
        "article_count": exact_count,
        "article_count_recent_7d": recent_count,
        "average_sentiment": latest.get("average_sentiment", 0.0),
        "average_sentiment_recent_7d": latest.get("average_sentiment_recent_7d", 0.0),
        "positive_article_ratio": latest.get("positive_article_ratio", 0.0),
        "negative_article_ratio": latest.get("negative_article_ratio", 0.0),
        "positive_article_ratio_recent_7d": latest.get("positive_article_ratio_recent_7d", 0.0),
        "negative_article_ratio_recent_7d": latest.get("negative_article_ratio_recent_7d", 0.0),
        "recent_headlines": payload.get("recent_headlines", []),
        "debug": {
            "fetched_article_count": payload.get("fetched_article_count", 0),
            "usable_article_count": payload.get("usable_article_count", 0),
            "matched_exact_days": payload.get("matched_exact_days", 0),
            "matched_recent_days": payload.get("matched_recent_days", 0),
        },
    }
