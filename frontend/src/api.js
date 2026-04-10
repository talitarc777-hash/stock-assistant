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

export async function fetchForecast(ticker, period = "2y") {
  return fetchJson(`/forecast?ticker=${encodeURIComponent(ticker)}&period=${period}`);
}

export async function fetchModelLatest(
  ticker,
  period = "5y",
  targetName = "target_5d_updown",
  modelName = "logistic_regression",
  userId = null
) {
  const userQuery = userId ? `&user_id=${encodeURIComponent(userId)}` : "";
  return fetchJson(
    `/model-latest?ticker=${encodeURIComponent(ticker)}&period=${period}&target_name=${encodeURIComponent(
      targetName
    )}&model_name=${encodeURIComponent(modelName)}${userQuery}`
  );
}

export async function fetchModelHistory(
  ticker,
  period = "5y",
  targetName = "target_5d_updown",
  modelName = "logistic_regression",
  limit = 200,
  userId = null
) {
  const userQuery = userId ? `&user_id=${encodeURIComponent(userId)}` : "";
  return fetchJson(
    `/model-history?ticker=${encodeURIComponent(ticker)}&period=${period}&target_name=${encodeURIComponent(
      targetName
    )}&model_name=${encodeURIComponent(modelName)}&limit=${limit}${userQuery}`
  );
}

export async function fetchModelAccuracy(
  ticker,
  period = "5y",
  targetName = "target_5d_updown",
  modelName = "logistic_regression",
  window = 20,
  userId = null
) {
  const userQuery = userId ? `&user_id=${encodeURIComponent(userId)}` : "";
  return fetchJson(
    `/model-accuracy?ticker=${encodeURIComponent(ticker)}&period=${period}&target_name=${encodeURIComponent(
      targetName
    )}&model_name=${encodeURIComponent(modelName)}&window=${window}${userQuery}`
  );
}

export async function fetchVirtualTraderSummary(
  ticker,
  period = "5y",
  modelName = "logistic_regression",
  equityLimit = 500,
  userId = null
) {
  const userQuery = userId ? `&user_id=${encodeURIComponent(userId)}` : "";
  return fetchJson(
    `/virtual-trader-summary?ticker=${encodeURIComponent(ticker)}&period=${period}&model_name=${encodeURIComponent(
      modelName
    )}&equity_limit=${equityLimit}${userQuery}`
  );
}

export async function fetchVirtualTraderTrades(
  ticker,
  period = "5y",
  modelName = "logistic_regression",
  limit = 200,
  userId = null
) {
  const userQuery = userId ? `&user_id=${encodeURIComponent(userId)}` : "";
  return fetchJson(
    `/virtual-trader-trades?ticker=${encodeURIComponent(ticker)}&period=${period}&model_name=${encodeURIComponent(
      modelName
    )}&limit=${limit}${userQuery}`
  );
}
