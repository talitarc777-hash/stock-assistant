import React, { useEffect, useMemo, useState } from "react";

import { fetchAnalyze, fetchChartData, fetchForecast, fetchWatchlistAnalyze } from "./api";
import LineChart from "./components/LineChart";
import WatchlistTable from "./components/WatchlistTable";
import { term } from "./i18n/terms";
import GlossaryPage from "./pages/GlossaryPage";
import "./styles.css";

const DEFAULT_WATCHLIST = ["VOO", "SPY", "QQQ", "AAPL", "MSFT", "NVDA"];
const DEFAULT_PERIOD = "5y";
const DASHBOARD_PATH = "/";
const GLOSSARY_PATH = "/glossary";
const LANGUAGE_STORAGE_KEY = "stock-assistant-language-mode";

function normalizePath(pathname) {
  return pathname === GLOSSARY_PATH ? GLOSSARY_PATH : DASHBOARD_PATH;
}

function getInitialLanguageMode() {
  const saved = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  if (saved === "en" || saved === "zh" || saved === "both") {
    return saved;
  }
  return "both";
}

function toNumeric(value) {
  if (value === null || value === undefined) {
    return Number.NaN;
  }
  const num = Number(value);
  return Number.isFinite(num) ? num : Number.NaN;
}

function navigateTo(path, setRoutePath) {
  const normalized = normalizePath(path);
  if (window.location.pathname !== normalized) {
    window.history.pushState({}, "", normalized);
  }
  setRoutePath(normalized);
}

function DashboardPage({ languageMode }) {
  const [watchlistRows, setWatchlistRows] = useState([]);
  const [selectedTicker, setSelectedTicker] = useState("VOO");
  const [analyzeData, setAnalyzeData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [isLoadingWatchlist, setIsLoadingWatchlist] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState("");

  async function loadWatchlist() {
    setIsLoadingWatchlist(true);
    setError("");
    try {
      const response = await fetchWatchlistAnalyze(DEFAULT_WATCHLIST, DEFAULT_PERIOD);
      const rankedRows = response.ranked_results || [];
      setWatchlistRows(rankedRows);
      if (rankedRows.length > 0) {
        const tickers = rankedRows.map((row) => row.ticker);
        if (!tickers.includes(selectedTicker)) {
          setSelectedTicker(tickers[0]);
        }
      }
    } catch (err) {
      setError(err.message || "Failed to load watchlist.");
    } finally {
      setIsLoadingWatchlist(false);
    }
  }

  async function loadTickerDetail(ticker) {
    if (!ticker) return;
    setIsLoadingDetail(true);
    setError("");
    try {
      const [analysis, chart] = await Promise.all([
        fetchAnalyze(ticker, DEFAULT_PERIOD),
        fetchChartData(ticker, DEFAULT_PERIOD),
      ]);
      let forecast = null;
      try {
        forecast = await fetchForecast(ticker, "2y");
      } catch {
        forecast = null;
      }
      setAnalyzeData(analysis);
      setChartData(chart);
      setForecastData(forecast);
    } catch (err) {
      setError(err.message || "Failed to load ticker detail.");
    } finally {
      setIsLoadingDetail(false);
    }
  }

  useEffect(() => {
    loadWatchlist();
  }, []);

  useEffect(() => {
    loadTickerDetail(selectedTicker);
  }, [selectedTicker]);

  const chartSeries = useMemo(() => {
    if (!chartData?.series) return [];
    return chartData.series.map((point) => ({
      date: point.date,
      close: toNumeric(point.close),
      sma_20: toNumeric(point.sma_20),
      sma_50: toNumeric(point.sma_50),
      sma_200: toNumeric(point.sma_200),
      rsi_14: toNumeric(point.rsi_14),
      macd_line: toNumeric(point.macd_line),
      macd_signal: toNumeric(point.macd_signal),
    }));
  }, [chartData]);

  const scoreSeries = useMemo(() => {
    if (!chartData?.score_series) return [];
    return chartData.score_series.map((point) => ({
      date: point.date,
      total_score: toNumeric(point.total_score),
    }));
  }, [chartData]);

  return (
    <>
      <header className="app-header">
        <div>
          <h1>{term("Dashboard", languageMode)}</h1>
          <p>
            {languageMode === "zh"
              ? "以 FastAPI 後端提供的簡潔決策輔助面板。"
              : languageMode === "en"
              ? "Simple decision-support view powered by the FastAPI backend."
              : "Simple decision-support view powered by the FastAPI backend. / 以 FastAPI 後端提供的簡潔決策輔助面板。"}
          </p>
        </div>
        <div className="header-controls">
          <label htmlFor="ticker-select">{term("Ticker", languageMode)}</label>
          <select
            id="ticker-select"
            value={selectedTicker}
            onChange={(event) => setSelectedTicker(event.target.value)}
          >
            {watchlistRows.map((row) => (
              <option key={row.ticker} value={row.ticker}>
                {row.ticker}
              </option>
            ))}
          </select>
          <button type="button" onClick={loadWatchlist} disabled={isLoadingWatchlist}>
            {isLoadingWatchlist ? `${term("Refresh", languageMode)}...` : term("Refresh", languageMode)}
          </button>
        </div>
      </header>

      {error ? <p className="error-box">{error}</p> : null}

      <div className="layout-grid">
        <WatchlistTable
          rows={watchlistRows}
          selectedTicker={selectedTicker}
          onSelectTicker={setSelectedTicker}
          languageMode={languageMode}
        />

        <section className="panel">
          <h3>{term("Ticker Detail", languageMode)}</h3>
          {isLoadingDetail || !analyzeData ? (
            <p>{term("Loading", languageMode)}...</p>
          ) : (
            <>
              <div className="detail-grid">
                <p>
                  <strong>{term("Ticker", languageMode)}:</strong> {analyzeData.ticker}
                </p>
                <p>
                  <strong>{term("Latest Close", languageMode)}:</strong>{" "}
                  {analyzeData.latest_close.toFixed(2)}
                </p>
                <p>
                  <strong>{term("Score", languageMode)}:</strong>{" "}
                  {analyzeData.score_breakdown.total_score}
                </p>
                <p>
                  <strong>{term("Label", languageMode)}:</strong> {analyzeData.label}
                </p>
                <p>
                  <strong>{term("Action Summary", languageMode)}:</strong>{" "}
                  {analyzeData.action_summary}
                </p>
                <p>
                  <strong>{term("Benchmark Strength", languageMode)}:</strong>{" "}
                  {analyzeData.benchmark_relative?.benchmark_strength_score ?? "N/A"}
                </p>
              </div>
              <h4>{term("Explanation", languageMode)}</h4>
              <ul className="bullet-list">
                {analyzeData.explanation_bullets.map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>
              <section className="forecast-card">
                <h4>{term("Forecast", languageMode)}</h4>
                <p className="helper-text">{term("Scenario-Based Forecast Only", languageMode)}</p>
                {!forecastData ? (
                  <p>{term("Loading", languageMode)}...</p>
                ) : (
                  <div className="forecast-grid">
                    <p>
                      <strong>{term("Trend Regime", languageMode)}:</strong>{" "}
                      {forecastData.trend_regime_en} / {forecastData.trend_regime_zh}
                    </p>
                    <p>
                      <strong>{term("5-Day Outlook", languageMode)}:</strong> {forecastData.outlook_5d}
                    </p>
                    <p>
                      <strong>{term("20-Day Outlook", languageMode)}:</strong> {forecastData.outlook_20d}
                    </p>
                    <p>
                      <strong>{term("Expected Range", languageMode)}:</strong>{" "}
                      {forecastData.expected_range?.lower?.toFixed(2)} -{" "}
                      {forecastData.expected_range?.upper?.toFixed(2)}
                    </p>
                    <p>
                      <strong>{term("Support", languageMode)}:</strong>{" "}
                      {forecastData.levels?.support_level?.toFixed(2)}
                    </p>
                    <p>
                      <strong>{term("Resistance", languageMode)}:</strong>{" "}
                      {forecastData.levels?.resistance_level?.toFixed(2)}
                    </p>
                    <p>
                      <strong>{term("Confidence Score", languageMode)}:</strong>{" "}
                      {forecastData.confidence_score}/100
                    </p>
                  </div>
                )}
              </section>
            </>
          )}
        </section>
      </div>

      <LineChart
        title={`${term("Price", languageMode)} + ${term("SMA", languageMode)}: SMA20 / SMA50 / SMA200`}
        points={chartSeries}
        overlays={{
          horizontalLines: [
            {
              key: "support",
              label: `${term("Support", languageMode)}`,
              value: toNumeric(forecastData?.levels?.support_level),
              color: "#0f766e",
            },
            {
              key: "resistance",
              label: `${term("Resistance", languageMode)}`,
              value: toNumeric(forecastData?.levels?.resistance_level),
              color: "#b45309",
            },
          ],
          rangeBand:
            forecastData && forecastData.expected_range
              ? {
                  key: "expected-range",
                  label: `${term("Expected Range", languageMode)}`,
                  lower: toNumeric(forecastData.expected_range.lower),
                  upper: toNumeric(forecastData.expected_range.upper),
                  color: "#2563eb",
                }
              : null,
        }}
        lines={[
          { key: "close", label: term("Close", languageMode), color: "#111827" },
          { key: "sma_20", label: "SMA20", color: "#2563eb" },
          { key: "sma_50", label: "SMA50", color: "#16a34a" },
          { key: "sma_200", label: "SMA200", color: "#d97706" },
        ]}
      />

      <div className="chart-grid">
        <LineChart
          title={`${term("RSI", languageMode)} (14)`}
          points={chartSeries}
          lines={[{ key: "rsi_14", label: "RSI14", color: "#7c3aed" }]}
          height={180}
        />
        <LineChart
          title={term("MACD", languageMode)}
          points={chartSeries}
          lines={[
            { key: "macd_line", label: "MACD", color: "#0f766e" },
            { key: "macd_signal", label: "Signal", color: "#dc2626" },
          ]}
          height={180}
        />
      </div>

      <LineChart
        title={term("Score Over Time", languageMode)}
        points={scoreSeries}
        lines={[{ key: "total_score", label: `Total ${term("Score", languageMode)}`, color: "#374151" }]}
        height={180}
      />
    </>
  );
}

export default function App() {
  const [routePath, setRoutePath] = useState(() => normalizePath(window.location.pathname));
  const [languageMode, setLanguageMode] = useState(getInitialLanguageMode);

  useEffect(() => {
    const onPopState = () => setRoutePath(normalizePath(window.location.pathname));
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, languageMode);
  }, [languageMode]);

  return (
    <main className="app-shell">
      <header className="panel global-header">
        <nav className="top-nav">
          <button
            type="button"
            className={routePath === DASHBOARD_PATH ? "nav-link active" : "nav-link"}
            onClick={() => navigateTo(DASHBOARD_PATH, setRoutePath)}
          >
            {term("Dashboard", languageMode)}
          </button>
          <button
            type="button"
            className={routePath === GLOSSARY_PATH ? "nav-link active" : "nav-link"}
            onClick={() => navigateTo(GLOSSARY_PATH, setRoutePath)}
          >
            {term("Glossary", languageMode)}
          </button>
        </nav>
        <div className="header-controls">
          <label htmlFor="global-lang-select">{term("Language", languageMode)}</label>
          <select
            id="global-lang-select"
            value={languageMode}
            onChange={(event) => setLanguageMode(event.target.value)}
          >
            <option value="en">English</option>
            <option value="zh">中文</option>
            <option value="both">English + 中文</option>
          </select>
        </div>
      </header>

      {routePath === GLOSSARY_PATH ? (
        <GlossaryPage languageMode={languageMode} />
      ) : (
        <DashboardPage languageMode={languageMode} />
      )}
    </main>
  );
}
