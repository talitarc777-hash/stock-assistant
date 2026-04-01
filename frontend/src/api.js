const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function fetchJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    const fallbackMessage = `Request failed with status ${response.status}`;
    let detail = fallbackMessage;
    try {
      const payload = await response.json();
      detail = payload?.detail || fallbackMessage;
    } catch {
      detail = fallbackMessage;
    }
    throw new Error(detail);
  }
  return response.json();
}

export async function fetchWatchlistAnalyze(tickers, period = "5y") {
  const joined = encodeURIComponent(tickers.join(","));
  return fetchJson(`/watchlist-analyze?tickers=${joined}&period=${period}`);
}

export async function fetchAnalyze(ticker, period = "5y") {
  return fetchJson(`/analyze?ticker=${encodeURIComponent(ticker)}&period=${period}`);
}

export async function fetchChartData(ticker, period = "5y") {
  return fetchJson(`/chart-data?ticker=${encodeURIComponent(ticker)}&period=${period}`);
}
