"""Simple company-name to ticker normalization helpers for the Discord bot."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TickerMatch:
    """Result of trying to resolve a plain-language stock name into tickers."""

    tickers: list[str]
    ambiguous: bool = False
    message: str | None = None


_NAME_TO_TICKER: dict[str, str] = {
    "tesla": "TSLA",
    "tesla stock": "TSLA",
    "apple": "AAPL",
    "apple stock": "AAPL",
    "apple inc": "AAPL",
    "microsoft": "MSFT",
    "microsoft stock": "MSFT",
    "microsoft corp": "MSFT",
    "microsoft corporation": "MSFT",
    "nvidia": "NVDA",
    "nvidia stock": "NVDA",
    "nvidia corp": "NVDA",
    "nvidia corporation": "NVDA",
    "amazon": "AMZN",
    "amazon stock": "AMZN",
    "amazon com": "AMZN",
    "meta": "META",
    "meta platforms": "META",
    "google": "GOOGL",
    "google stock": "GOOGL",
    "alphabet": "GOOGL",
    "alphabet stock": "GOOGL",
    "amazon com inc": "AMZN",
    "vanguard s p 500 etf": "VOO",
    "vanguard sp 500 etf": "VOO",
    "vanguard s p 500": "VOO",
    "vanguard sp 500": "VOO",
    "s p 500 etf": "VOO",
    "sp 500 etf": "VOO",
    "spy": "SPY",
    "qqq": "QQQ",
    "voo": "VOO",
}

_AMBIGUOUS_NAMES: dict[str, str] = {
    "vanguard": "I found more than one possible Vanguard match. Please use the ticker symbol.",
    "s p 500": "I found more than one S&P 500 match. Please use the ticker symbol.",
    "sp 500": "I found more than one S&P 500 match. Please use the ticker symbol.",
}

_KNOWN_TICKERS = set(_NAME_TO_TICKER.values()) | {"AMD", "IBM", "INTC", "NFLX", "TSM"}

_COMMON_WORDS = {
    "ADD",
    "ABOUT",
    "AND",
    "ANALYZE",
    "ANALYSIS",
    "CHECK",
    "DELETE",
    "DISABLE",
    "ENGLISH",
    "FORECAST",
    "FOR",
    "GET",
    "HELP",
    "INTO",
    "IN",
    "IS",
    "LANGUAGE",
    "ME",
    "MODE",
    "MY",
    "OF",
    "ON",
    "OUTLOOK",
    "OR",
    "PLEASE",
    "PREDICT",
    "PUT",
    "REMOVE",
    "REPLY",
    "SETTINGS",
    "SET",
    "SHOW",
    "SHORT",
    "SPEAK",
    "STOCK",
    "THE",
    "TO",
    "TURN",
    "USE",
    "WATCHLIST",
    "WHAT",
    "WITH",
}


def _normalize_phrase(value: str) -> str:
    """Lowercase a phrase and remove punctuation so name matching stays simple."""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", " ", str(value).strip().lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _extract_ticker_symbols(text: str) -> list[str]:
    """Extract ticker-like tokens without turning ordinary words into tickers."""
    tokens = re.findall(r"\b[A-Za-z]{1,5}\b", text)
    seen: set[str] = set()
    tickers: list[str] = []
    for token in tokens:
        upper = token.upper()
        if upper in _COMMON_WORDS:
            continue
        if upper in _KNOWN_TICKERS:
            looks_like_ticker = True
        else:
            looks_like_ticker = token.isalpha() and len(token) <= 5
        if not looks_like_ticker:
            continue
        if (not token.isupper()) and upper not in _KNOWN_TICKERS and len(token) > 4:
            continue
        if upper in seen:
            continue
        seen.add(upper)
        tickers.append(upper)
    return tickers


def resolve_ticker_phrase(phrase: str) -> TickerMatch:
    """Resolve one short user phrase into ticker symbols if possible."""
    normalized = _normalize_phrase(phrase)
    if not normalized:
        return TickerMatch(tickers=[])

    if normalized in _AMBIGUOUS_NAMES:
        return TickerMatch(tickers=[], ambiguous=True, message=_AMBIGUOUS_NAMES[normalized])

    if normalized in _NAME_TO_TICKER:
        return TickerMatch(tickers=[_NAME_TO_TICKER[normalized]])

    ticker_tokens = _extract_ticker_symbols(phrase)
    if len(ticker_tokens) == 1:
        return TickerMatch(tickers=ticker_tokens)
    if len(ticker_tokens) > 1:
        return TickerMatch(tickers=ticker_tokens)

    return TickerMatch(tickers=[])


def extract_tickers_from_text(text: str) -> TickerMatch:
    """Extract one or more tickers from a natural-language message."""
    normalized = _normalize_phrase(text)
    if not normalized:
        return TickerMatch(tickers=[])

    for ambiguous_name, message in _AMBIGUOUS_NAMES.items():
        if ambiguous_name in normalized:
            return TickerMatch(tickers=[], ambiguous=True, message=message)

    found: list[str] = []
    name_matches: list[tuple[int, str]] = []

    for company_name, ticker in _NAME_TO_TICKER.items():
        position = normalized.find(company_name)
        if position >= 0:
            name_matches.append((position, ticker))

    for _, ticker in sorted(name_matches, key=lambda item: item[0]):
        if ticker not in found:
            found.append(ticker)

    for ticker in _extract_ticker_symbols(text):
        if ticker not in found:
            found.append(ticker)

    return TickerMatch(tickers=found)
