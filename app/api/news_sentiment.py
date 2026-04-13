"""News sentiment latest/debug endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.news_debug_service import (
    build_news_sentiment_debug,
    get_latest_news_sentiment,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["news-sentiment"])


class NewsSentimentLatestResponse(BaseModel):
    ticker: str
    period: str
    status: str
    message_en: str
    message_zh: str
    article_count: int
    article_count_recent_7d: int
    average_sentiment: float
    average_sentiment_recent_7d: float
    positive_article_ratio: float
    negative_article_ratio: float
    positive_article_ratio_recent_7d: float
    negative_article_ratio_recent_7d: float
    recent_headlines: list[str]
    debug: dict


class NewsSentimentDebugResponse(BaseModel):
    ticker: str
    requested_date: str | None
    period: str
    sentiment_model: str
    fetched_article_count: int
    usable_article_count: int
    matched_exact_days: int
    matched_recent_days: int
    latest_feature_row: dict
    recent_headlines: list[str]


@router.get("/news-sentiment/latest", response_model=NewsSentimentLatestResponse)
def news_sentiment_latest(
    ticker: str = Query(..., min_length=1, max_length=15),
    period: str = Query("6mo", min_length=2, max_length=10),
) -> NewsSentimentLatestResponse:
    """Return latest news sentiment snapshot for one ticker."""
    try:
        payload = get_latest_news_sentiment(ticker=ticker, period=period)
        return NewsSentimentLatestResponse(**payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected news sentiment latest error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.get("/news-sentiment/debug", response_model=NewsSentimentDebugResponse)
def news_sentiment_debug(
    ticker: str = Query(..., min_length=1, max_length=15),
    date: str | None = Query(default=None),
    period: str = Query("6mo", min_length=2, max_length=10),
    sentiment_model: str = Query("finbert", min_length=2, max_length=20),
) -> NewsSentimentDebugResponse:
    """Return detailed end-to-end debug data for the news pipeline."""
    try:
        payload = build_news_sentiment_debug(
            ticker=ticker,
            date=date,
            period=period,
            sentiment_model=sentiment_model,
        )
        return NewsSentimentDebugResponse(**payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected news sentiment debug error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc
