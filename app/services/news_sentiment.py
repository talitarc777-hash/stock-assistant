"""News preprocessing + sentiment scoring + daily aggregation features."""

from __future__ import annotations

import logging
import re
from typing import Protocol

import pandas as pd

from app.services.news_service import (
    NewsProvider,
    YahooFinanceNewsProvider,
    articles_to_frame,
)
logger = logging.getLogger(__name__)


class NewsSentimentError(Exception):
    """Base exception for news sentiment processing."""


class SentimentScorer(Protocol):
    """Simple scorer interface so models can be swapped later."""

    def score_texts(self, texts: list[str]) -> list[float]:
        """Return a sentiment score per text in [-1, 1]."""

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


def _score_text_sentiment_lexicon(text: str) -> float:
    """Score text with a very small keyword lexicon."""
    tokens = re.findall(r"[A-Za-z']+", text.lower())
    if not tokens:
        return 0.0

    positive_hits = sum(1 for token in tokens if token in _POSITIVE_WORDS)
    negative_hits = sum(1 for token in tokens if token in _NEGATIVE_WORDS)
    return (positive_hits - negative_hits) / max(len(tokens), 1)


class LexiconSentimentScorer:
    """Beginner-friendly fallback scorer when FinBERT is unavailable."""

    def score_texts(self, texts: list[str]) -> list[float]:
        return [_score_text_sentiment_lexicon(text) for text in texts]


class FinBertSentimentScorer:
    """
    Finance-domain sentiment scorer backed by ProsusAI/finbert.

    Notes:
    - This class lazy-loads `transformers` so the project still runs without it.
    - If model loading fails, callers can fallback to `LexiconSentimentScorer`.
    """

    def __init__(self, model_name: str = "ProsusAI/finbert") -> None:
        try:
            from transformers import pipeline  # type: ignore
        except Exception as exc:  # pragma: no cover - dependency availability varies
            raise NewsSentimentError(
                "FinBERT dependencies are unavailable. Install `transformers` (and a backend like `torch`)."
            ) from exc

        try:
            self._pipeline = pipeline(
                task="text-classification",
                model=model_name,
                tokenizer=model_name,
            )
        except Exception as exc:  # pragma: no cover - model download/runtime varies
            raise NewsSentimentError(f"Failed to load FinBERT model '{model_name}'.") from exc

    def score_texts(self, texts: list[str]) -> list[float]:
        if not texts:
            return []

        results = self._pipeline(texts, truncation=True, max_length=256)
        scores: list[float] = []
        for item in results:
            label = str(item.get("label", "")).lower()
            confidence = float(item.get("score", 0.0))
            if "positive" in label:
                scores.append(confidence)
            elif "negative" in label:
                scores.append(-confidence)
            else:
                scores.append(0.0)
        return scores


def _build_scorer(
    sentiment_model: str = "finbert",
    fallback_to_lexicon: bool = True,
) -> SentimentScorer:
    """Build the requested scorer with optional safe fallback."""
    if sentiment_model.strip().lower() != "finbert":
        return LexiconSentimentScorer()

    try:
        return FinBertSentimentScorer()
    except NewsSentimentError as exc:
        if not fallback_to_lexicon:
            raise
        logger.warning("FinBERT unavailable, fallback to lexicon scorer: %s", exc)
        return LexiconSentimentScorer()


def _score_articles(
    article_df: pd.DataFrame,
    scorer: SentimentScorer,
) -> pd.DataFrame:
    """Attach sentiment score and polarity label to article metadata rows."""
    result = article_df.copy()
    scores = scorer.score_texts(result["title"].fillna("").astype(str).tolist())
    result["sentiment_score"] = scores
    result["sentiment_label"] = "neutral"
    result.loc[result["sentiment_score"] > 0.05, "sentiment_label"] = "positive"
    result.loc[result["sentiment_score"] < -0.05, "sentiment_label"] = "negative"
    return result


def _aggregate_daily_features(
    scored_article_df: pd.DataFrame,
    date_index: pd.Series,
    mapped_ticker: str,
) -> pd.DataFrame:
    """Aggregate article-level sentiment into daily ticker-level features."""
    base = pd.DataFrame({"date": pd.to_datetime(date_index, utc=False)}).copy()
    base["ticker"] = mapped_ticker
    base["article_count"] = 0
    base["average_sentiment"] = 0.0
    base["positive_article_ratio"] = 0.0
    base["negative_article_ratio"] = 0.0
    base["article_count_recent_7d"] = 0
    base["average_sentiment_recent_7d"] = 0.0
    base["positive_article_ratio_recent_7d"] = 0.0
    base["negative_article_ratio_recent_7d"] = 0.0

    if scored_article_df.empty:
        return base

    daily = scored_article_df.copy()
    daily["date"] = pd.to_datetime(daily["article_date"], errors="coerce")
    daily = daily.dropna(subset=["date"]).sort_values("date")

    grouped = (
        daily.groupby("date", as_index=False)
        .agg(
            article_count=("title", "count"),
            average_sentiment=("sentiment_score", "mean"),
            positive_count=("sentiment_label", lambda values: int((values == "positive").sum())),
            negative_count=("sentiment_label", lambda values: int((values == "negative").sum())),
        )
    )
    grouped["positive_article_ratio"] = grouped["positive_count"] / grouped["article_count"]
    grouped["negative_article_ratio"] = grouped["negative_count"] / grouped["article_count"]

    merged = base.merge(grouped, on="date", how="left", suffixes=("", "_agg"))
    for column in ("article_count", "average_sentiment", "positive_article_ratio", "negative_article_ratio"):
        agg_column = f"{column}_agg"
        if agg_column in merged.columns:
            merged[column] = merged[agg_column].fillna(merged[column])
            merged = merged.drop(columns=[agg_column])

    # Build a trailing 7-day view so "recent news" is available even when
    # there is no exact same-day headline on a trading date.
    rolling_base = merged[["date"]].copy().set_index("date")
    grouped_indexed = grouped.set_index("date").reindex(rolling_base.index).fillna(0.0)
    grouped_indexed["weighted_sentiment"] = (
        grouped_indexed["average_sentiment"] * grouped_indexed["article_count"]
    )
    grouped_indexed["article_count_recent_7d"] = (
        grouped_indexed["article_count"].rolling(window=7, min_periods=1).sum()
    )
    grouped_indexed["positive_count_recent_7d"] = (
        grouped_indexed["positive_count"].rolling(window=7, min_periods=1).sum()
    )
    grouped_indexed["negative_count_recent_7d"] = (
        grouped_indexed["negative_count"].rolling(window=7, min_periods=1).sum()
    )
    grouped_indexed["weighted_sentiment_recent_7d"] = (
        grouped_indexed["weighted_sentiment"].rolling(window=7, min_periods=1).sum()
    )
    grouped_indexed["average_sentiment_recent_7d"] = grouped_indexed.apply(
        lambda row: (
            row["weighted_sentiment_recent_7d"] / row["article_count_recent_7d"]
            if row["article_count_recent_7d"] > 0
            else 0.0
        ),
        axis=1,
    )
    grouped_indexed["positive_article_ratio_recent_7d"] = grouped_indexed.apply(
        lambda row: (
            row["positive_count_recent_7d"] / row["article_count_recent_7d"]
            if row["article_count_recent_7d"] > 0
            else 0.0
        ),
        axis=1,
    )
    grouped_indexed["negative_article_ratio_recent_7d"] = grouped_indexed.apply(
        lambda row: (
            row["negative_count_recent_7d"] / row["article_count_recent_7d"]
            if row["article_count_recent_7d"] > 0
            else 0.0
        ),
        axis=1,
    )

    merged = merged.merge(
        grouped_indexed[
            [
                "article_count_recent_7d",
                "average_sentiment_recent_7d",
                "positive_article_ratio_recent_7d",
                "negative_article_ratio_recent_7d",
            ]
        ].reset_index(),
        on="date",
        how="left",
        suffixes=("", "_rolling"),
    )
    for column in (
        "article_count_recent_7d",
        "average_sentiment_recent_7d",
        "positive_article_ratio_recent_7d",
        "negative_article_ratio_recent_7d",
    ):
        rolling_column = f"{column}_rolling"
        if rolling_column in merged.columns:
            merged[column] = merged[rolling_column].fillna(merged[column])
            merged = merged.drop(columns=[rolling_column])

    merged["article_count"] = merged["article_count"].astype(int)
    merged["article_count_recent_7d"] = merged["article_count_recent_7d"].astype(int)
    return merged


def build_daily_news_features(
    ticker: str,
    date_index: pd.Series,
    company_name: str | None = None,
    provider: NewsProvider | None = None,
    sentiment_model: str = "finbert",
    fallback_to_lexicon: bool = True,
) -> pd.DataFrame:
    """
    Build daily ticker-level news sentiment features for model datasets.

    Notes:
    - Article metadata ingestion is source-agnostic via the provider interface.
    - Sentiment supports FinBERT and falls back to lexicon scoring by default.
    - Missing days are filled with zeros for beginner-friendly downstream usage.
    """
    ticker_symbol = ticker.strip().upper()
    news_provider = provider or YahooFinanceNewsProvider()
    scorer = _build_scorer(
        sentiment_model=sentiment_model,
        fallback_to_lexicon=fallback_to_lexicon,
    )

    try:
        articles = news_provider.fetch_article_metadata(
            ticker=ticker_symbol,
            company_name=company_name,
        )
        logger.info(
            "News fetch completed ticker=%s company=%s fetched_articles=%d",
            ticker_symbol,
            company_name or "",
            len(articles),
        )
    except Exception as exc:  # pragma: no cover - provider failures vary by environment
        logger.warning(
            "News metadata fetch failed for ticker=%s company=%s: %s",
            ticker_symbol,
            company_name,
            exc,
        )
        return _aggregate_daily_features(
            scored_article_df=pd.DataFrame(),
            date_index=date_index,
            mapped_ticker=ticker_symbol,
        )

    article_df = articles_to_frame(articles)
    if article_df.empty:
        logger.info("News fetch returned no usable rows ticker=%s", ticker_symbol)
        return _aggregate_daily_features(
            scored_article_df=pd.DataFrame(),
            date_index=date_index,
            mapped_ticker=ticker_symbol,
        )

    scored_df = _score_articles(article_df=article_df, scorer=scorer)
    features_df = _aggregate_daily_features(
        scored_article_df=scored_df,
        date_index=date_index,
        mapped_ticker=ticker_symbol,
    )
    matched_rows = int((features_df["article_count"] > 0).sum())
    matched_recent_rows = int((features_df["article_count_recent_7d"] > 0).sum())
    logger.info(
        "News aggregation ticker=%s article_rows=%d matched_exact_days=%d matched_recent_days=%d",
        ticker_symbol,
        len(scored_df),
        matched_rows,
        matched_recent_rows,
    )
    return features_df
