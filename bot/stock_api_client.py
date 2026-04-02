import requests
from config import BACKEND_BASE_URL

def analyze(ticker: str):
    url = f"{BACKEND_BASE_URL}/analyze?ticker={ticker}"
    return requests.get(url, timeout=10).json()

def forecast(ticker: str):
    url = f"{BACKEND_BASE_URL}/forecast?ticker={ticker}"
    return requests.get(url, timeout=10).json()

def watchlist():
    url = f"{BACKEND_BASE_URL}/watchlist-analyze"
    return requests.get(url, timeout=10).json()