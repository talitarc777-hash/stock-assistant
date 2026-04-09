"""Lightweight Yahoo news sentiment features for research datasets."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


NewsFetcher = Callable[[str], list[dict]]

_POSITIVE_WORDS: set[str] = {
    "beat",
    "beats",
    "breakout",
    "bullish",
    "buy",
    "confidence",
    "gain",
    "gains",
    "growth",
    "improve",
    "improves",
    "improving",
    "momentum",
    "optimistic",
    "outperform",
    "outperforms",
    "positive",
    "rally",
    "rebound",
    "record",
    "rise",
    "rises",
    "strong",
    "surge",
    "upside",
}

_NEGATIVE_WORDS: set[str] = {
    "bearish",
    "below",
    "concern",
    "concerns",
    "cut",
    "cuts",
    "decline",
    "declines",
    "downgrade",
    "downgrades",
    "drop",
    "drops",
    "fall",
    "falls",
    "loss",
    "losses",
    "miss",
    "misses",
    "negative",
    "pressure",
    "reduce",
    "reduced",
    "recession",
    "risk",
    "risks",
    "selloff",
    "slump",
    "soft",
    "volatile",
    "warning",
    "weak",
}


def _default_fetch_news(ticker: str) -> list[dict]:
    """Fetch recent Yahoo Finance news items for a ticker."""
    return list(yf.Ticker(ticker).news or [])


def _extract_publish_datetime(item: dict) -> pd.Timestamp | None:
    """Extract a publish timestamp from multiple possible Yahoo news shapes."""
    timestamp = item.get("providerPublishTime")
    if timestamp:
        return pd.to_datetime(timestamp, unit="s", utc=True, errors="coerce")

    content = item.get("content")
    if isinstance(content, dict):
        for key in ("pubDate", "published", "publishTime"):
            if content.get(key):
                return pd.to_datetime(content[key], utc=True, errors="coerce")

    for key in ("pubDate", "published"):
        if item.get(key):
            return pd.to_datetime(item[key], utc=True, errors="coerce")

    return None


def _extract_text(item: dict) -> str:
    """Combine headline-like fields into one text block for simple scoring."""
    pieces: list[str] = []

    for key in ("title", "summary"):
        value = item.get(key)
        if isinstance(value, str):
            pieces.append(value)

    content = item.get("content")
    if isinstance(content, dict):
        for key in ("title", "summary", "description"):
            value = content.get(key)
            if isinstance(value, str):
                pieces.append(value)

    return " ".join(piece.strip() for piece in pieces if piece and piece.strip())


def _score_text_sentiment(text: str) -> float:
    """Score text with a very small keyword lexicon."""
    tokens = re.findall(r"[A-Za-z']+", text.lower())
    if not tokens:
        return 0.0

    positive_hits = sum(1 for token in tokens if token in _POSITIVE_WORDS)
    negative_hits = sum(1 for token in tokens if token in _NEGATIVE_WORDS)
    return (positive_hits - negative_hits) / max(len(tokens), 1)


def build_news_sentiment_features(
    ticker: str,
    date_index: pd.Series,
    news_fetcher: NewsFetcher | None = None,
) -> pd.DataFrame:
    """
    Build daily news sentiment features aligned to a dataset date column.

    Notes:
    - Yahoo Finance news availability can be sparse and is usually recent-only.
    - Missing days are filled with zeros so the downstream dataset stays easy to use.
    """
    features = pd.DataFrame({"date": pd.to_datetime(date_index, utc=False)}).copy()

    features["news_article_count"] = 0
    features["news_sentiment_score"] = 0.0
    features["news_sentiment_3d_avg"] = 0.0
    features["news_sentiment_7d_avg"] = 0.0

    fetcher = news_fetcher or _default_fetch_news

    try:
        raw_items = fetcher(ticker)
    except Exception as exc:  # pragma: no cover - provider failures are environment-dependent
        logger.warning("Failed to fetch news for ticker=%s: %s", ticker, exc)
        return features

    records: list[dict[str, object]] = []
    for item in raw_items:
        published_at = _extract_publish_datetime(item)
        article_text = _extract_text(item)
        if published_at is None or not article_text:
            continue

        published_date = published_at.tz_convert(None).normalize()
        records.append(
            {
                "date": published_date,
                "news_sentiment_score": _score_text_sentiment(article_text),
                "news_article_count": 1,
            }
        )

    if not records:
        return features

    news_df = pd.DataFrame(records)
    grouped = (
        news_df.groupby("date", as_index=False)
        .agg(
            news_article_count=("news_article_count", "sum"),
            news_sentiment_score=("news_sentiment_score", "mean"),
        )
        .sort_values("date")
    )

    merged = features.merge(grouped, on="date", how="left", suffixes=("", "_fetched"))
    if "news_article_count_fetched" in merged.columns:
        merged["news_article_count"] = (
            merged["news_article_count_fetched"].fillna(merged["news_article_count"]).astype(int)
        )
        merged = merged.drop(columns=["news_article_count_fetched"])
    if "news_sentiment_score_fetched" in merged.columns:
        merged["news_sentiment_score"] = merged["news_sentiment_score_fetched"].fillna(
            merged["news_sentiment_score"]
        )
        merged = merged.drop(columns=["news_sentiment_score_fetched"])

    merged["news_sentiment_3d_avg"] = (
        merged["news_sentiment_score"].rolling(window=3, min_periods=1).mean()
    )
    merged["news_sentiment_7d_avg"] = (
        merged["news_sentiment_score"].rolling(window=7, min_periods=1).mean()
    )

    return merged
