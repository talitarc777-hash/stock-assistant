import requests
from config import BACKEND_BASE_URL


def _get_json(url: str):
    """Perform GET request and return parsed JSON with clear API errors."""
    response = requests.get(url, timeout=15)
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if response.status_code >= 400:
        detail = payload.get("detail", f"HTTP {response.status_code}")
        raise RuntimeError(detail)
    return payload


def analyze(ticker: str):
    url = f"{BACKEND_BASE_URL}/analyze?ticker={ticker}"
    return _get_json(url)


def forecast(ticker: str, period: str = "2y"):
    url = f"{BACKEND_BASE_URL}/forecast?ticker={ticker}&period={period}"
    return _get_json(url)


def watchlist(tickers_csv: str, period: str = "5y"):
    url = f"{BACKEND_BASE_URL}/watchlist-analyze?tickers={tickers_csv}&period={period}"
    return _get_json(url)
