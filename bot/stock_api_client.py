import requests
from config import BACKEND_BASE_URL


class ApiClientError(Exception):
    """Base API client error for Discord bot messaging."""


class InvalidTickerApiError(ApiClientError):
    """Raised when backend reports an invalid ticker or bad ticker query."""


class BackendUnavailableError(ApiClientError):
    """Raised when backend cannot be reached."""


class BackendTimeoutError(ApiClientError):
    """Raised when backend request times out."""


def _get_json(url: str):
    """Perform GET request and return parsed JSON with clear API errors."""
    try:
        response = requests.get(url, timeout=15)
    except requests.exceptions.Timeout as exc:
        raise BackendTimeoutError("Backend request timed out.") from exc
    except requests.exceptions.ConnectionError as exc:
        raise BackendUnavailableError("Backend is unavailable.") from exc
    except requests.exceptions.RequestException as exc:
        raise ApiClientError("Backend request failed.") from exc

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if response.status_code >= 400:
        detail = str(payload.get("detail", f"HTTP {response.status_code}"))
        detail_lower = detail.lower()

        if response.status_code in (400, 404, 422) and (
            "ticker" in detail_lower or "symbol" in detail_lower
        ):
            raise InvalidTickerApiError(detail)

        if response.status_code >= 500:
            raise BackendUnavailableError(detail)

        raise ApiClientError(detail)
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


def chart_data(ticker: str, period: str = "6mo"):
    """Fetch chart + indicator history for one ticker from backend."""
    url = f"{BACKEND_BASE_URL}/chart-data?ticker={ticker}&period={period}"
    return _get_json(url)
