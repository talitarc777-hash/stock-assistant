"""News ingestion service layer for ticker/company article metadata."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Protocol

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class NewsServiceError(Exception):
    """Base error for news service operations."""


@dataclass(frozen=True)
class NewsArticle:
    """Normalized news article metadata for downstream processing."""

    article_date: pd.Timestamp
    title: str
    source: str
    mapped_ticker: str
    query: str
    url: str = ""


class NewsProvider(Protocol):
    """Provider interface to keep news data source swappable."""

    def fetch_article_metadata(
        self,
        ticker: str | None = None,
        company_name: str | None = None,
        limit: int = 100,
    ) -> list[NewsArticle]:
        """Fetch and normalize article metadata for ticker or company."""


def _normalize_text(value: object) -> str:
    """Safely normalize arbitrary values to stripped strings."""
    if value is None:
        return ""
    return str(value).strip()


def _extract_source(raw_item: dict) -> str:
    """Extract source/provider name from possible Yahoo news shapes."""
    source = _normalize_text(raw_item.get("publisher"))
    if source:
        return source

    content = raw_item.get("content")
    if isinstance(content, dict):
        provider = content.get("provider")
        if isinstance(provider, dict):
            source = _normalize_text(provider.get("displayName") or provider.get("name"))
            if source:
                return source

    return "unknown"


def _extract_title(raw_item: dict) -> str:
    """Extract title from multiple possible fields."""
    title = _normalize_text(raw_item.get("title"))
    if title:
        return title

    content = raw_item.get("content")
    if isinstance(content, dict):
        title = _normalize_text(content.get("title"))
        if title:
            return title

    return ""


def _extract_url(raw_item: dict) -> str:
    """Extract article URL from multiple possible fields."""
    direct_link = _normalize_text(raw_item.get("link"))
    if direct_link:
        return direct_link

    content = raw_item.get("content")
    if isinstance(content, dict):
        canonical = content.get("canonicalUrl")
        if isinstance(canonical, dict):
            return _normalize_text(canonical.get("url"))
    return ""


def _extract_publish_date(raw_item: dict) -> pd.Timestamp | None:
    """Extract publish datetime from Yahoo-like responses."""
    if raw_item.get("providerPublishTime"):
        return pd.to_datetime(raw_item["providerPublishTime"], unit="s", utc=True, errors="coerce")

    content = raw_item.get("content")
    if isinstance(content, dict):
        for key in ("pubDate", "published", "publishTime"):
            if content.get(key):
                return pd.to_datetime(content[key], utc=True, errors="coerce")

    for key in ("pubDate", "published"):
        if raw_item.get(key):
            return pd.to_datetime(raw_item[key], utc=True, errors="coerce")

    return None


def resolve_ticker_for_company(company_name: str) -> str | None:
    """Best-effort company-to-ticker resolution using yfinance search."""
    clean_name = _normalize_text(company_name)
    if not clean_name:
        return None

    search_cls = getattr(yf, "Search", None)
    if search_cls is None:
        return None

    try:
        search = search_cls(clean_name, max_results=5, news_count=0)
        quotes = getattr(search, "quotes", []) or []
        for quote in quotes:
            symbol = _normalize_text(quote.get("symbol")).upper()
            if symbol:
                return symbol
    except Exception as exc:  # pragma: no cover - environment/network dependent
        logger.warning("Company ticker resolution failed for %s: %s", clean_name, exc)

    return None


class YahooFinanceNewsProvider:
    """Yahoo Finance-backed provider for ticker/company news metadata."""

    def fetch_article_metadata(
        self,
        ticker: str | None = None,
        company_name: str | None = None,
        limit: int = 100,
    ) -> list[NewsArticle]:
        clean_ticker = _normalize_text(ticker).upper()
        clean_company = _normalize_text(company_name)

        if not clean_ticker and not clean_company:
            raise NewsServiceError("Provide at least one of ticker or company_name.")

        mapped_ticker = clean_ticker or resolve_ticker_for_company(clean_company) or clean_company.upper()
        query = clean_ticker or clean_company

        raw_items: list[dict]
        try:
            if clean_ticker:
                raw_items = list(yf.Ticker(clean_ticker).news or [])
            else:
                search_cls = getattr(yf, "Search", None)
                if search_cls is None:
                    raise NewsServiceError(
                        "Company search is unavailable in this yfinance version. Use ticker input."
                    )
                search = search_cls(clean_company, max_results=8, news_count=limit)
                raw_items = list(getattr(search, "news", []) or [])
        except NewsServiceError:
            raise
        except Exception as exc:  # pragma: no cover - provider failures vary by environment
            raise NewsServiceError(f"Failed to fetch news for query '{query}'.") from exc

        normalized_articles: list[NewsArticle] = []
        for raw_item in raw_items[: max(limit, 1)]:
            publish_dt = _extract_publish_date(raw_item)
            title = _extract_title(raw_item)
            if publish_dt is None or not title:
                continue

            normalized_articles.append(
                NewsArticle(
                    article_date=publish_dt.tz_convert(None).normalize(),
                    title=title,
                    source=_extract_source(raw_item),
                    mapped_ticker=mapped_ticker,
                    query=query,
                    url=_extract_url(raw_item),
                )
            )

        return normalized_articles


def articles_to_frame(articles: list[NewsArticle]) -> pd.DataFrame:
    """Convert normalized article metadata to a predictable DataFrame."""
    if not articles:
        return pd.DataFrame(
            columns=[
                "article_date",
                "title",
                "source",
                "mapped_ticker",
                "query",
                "url",
            ]
        )

    frame = pd.DataFrame([article.__dict__ for article in articles])
    frame["article_date"] = pd.to_datetime(frame["article_date"], errors="coerce")
    frame = frame.dropna(subset=["article_date"]).sort_values("article_date").reset_index(drop=True)
    return frame
