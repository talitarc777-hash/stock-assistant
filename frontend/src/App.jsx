import React, { useEffect, useMemo, useState } from "react";

import { fetchAnalyze, fetchChartData, fetchForecast, fetchWatchlistAnalyze } from "./api";
import LineChart from "./components/LineChart";
import WatchlistTable from "./components/WatchlistTable";
import { term } from "./i18n/terms";
import "./styles.css";

const DEFAULT_WATCHLIST = ["VOO", "SPY", "QQQ", "AAPL", "MSFT", "NVDA"];
const DEFAULT_PERIOD = "5y";

function toNumeric(value) {
  if (value === null || value === undefined) {
    return Number.NaN;
  }
  const num = Number(value);
  return Number.isFinite(num) ? num : Number.NaN;
}

export default function App() {
  const [watchlistRows, setWatchlistRows] = useState([]);
  const [selectedTicker, setSelectedTicker] = useState("VOO");
  const [analyzeData, setAnalyzeData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [isLoadingWatchlist, setIsLoadingWatchlist] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState("");
  const [languageMode, setLanguageMode] = useState("both");

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
      const [analysis, chart, forecast] = await Promise.all([
        fetchAnalyze(ticker, DEFAULT_PERIOD),
        fetchChartData(ticker, DEFAULT_PERIOD),
        fetchForecast(ticker, "2y"),
      ]);
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
    <main className="app-shell">
      <header className="app-header">
        <div>
          <h1>Stock Assistant Dashboard</h1>
          <p>Simple decision-support view powered by the FastAPI backend.</p>
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
          <label htmlFor="lang-select">Language</label>
          <select
            id="lang-select"
            value={languageMode}
            onChange={(event) => setLanguageMode(event.target.value)}
          >
            <option value="both">EN + 中文</option>
            <option value="en">EN</option>
            <option value="zh">中文</option>
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
            <p>Loading ticker details...</p>
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
                  <strong>Benchmark Strength:</strong>{" "}
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
                <h4>{term("Forecast", "both")}</h4>
                <p className="helper-text">
                  Scenario-based forecast only
                  <br />
                  情景分析，並非保證預測
                </p>
                {!forecastData ? (
                  <p>Loading forecast...</p>
                ) : (
                  <div className="forecast-grid">
                    <p>
                      <strong>{term("Trend Regime", "both")}:</strong>{" "}
                      {forecastData.trend_regime_en} / {forecastData.trend_regime_zh}
                    </p>
                    <p>
                      <strong>{term("5-Day Outlook", "both")}:</strong>{" "}
                      {forecastData.outlook_5d}
                    </p>
                    <p>
                      <strong>{term("20-Day Outlook", "both")}:</strong>{" "}
                      {forecastData.outlook_20d}
                    </p>
                    <p>
                      <strong>{term("Expected Range", "both")}:</strong>{" "}
                      {forecastData.expected_range?.lower?.toFixed(2)} -{" "}
                      {forecastData.expected_range?.upper?.toFixed(2)}
                    </p>
                    <p>
                      <strong>{term("Support", "both")}:</strong>{" "}
                      {forecastData.levels?.support_level?.toFixed(2)}
                    </p>
                    <p>
                      <strong>{term("Resistance", "both")}:</strong>{" "}
                      {forecastData.levels?.resistance_level?.toFixed(2)}
                    </p>
                    <p>
                      <strong>{term("Confidence Score", "both")}:</strong>{" "}
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
        lines={[
          { key: "close", label: "Close", color: "#111827" },
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
    </main>
  );
}

