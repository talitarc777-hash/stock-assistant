import React, { useEffect, useMemo, useState } from "react";

import { fetchAnalyze, fetchChartData, fetchForecast, fetchWatchlistAnalyze } from "./api";
import LineChart from "./components/LineChart";
import WatchlistManager from "./components/WatchlistManager";
import WatchlistTable from "./components/WatchlistTable";
import GlossaryPage from "./pages/GlossaryPage";
import SettingsPage from "./pages/SettingsPage";
import {
  fetchUserAlertScan,
  fetchUserProfile,
  fetchUserWatchlist,
  updateUserProfileSettings,
} from "./services/userProfileApi";
import "./styles.css";

const DEFAULT_PERIOD = "5y";
const DASHBOARD_PATH = "/";
const GLOSSARY_PATH = "/glossary";
const SETTINGS_PATH = "/settings";
const LANGUAGE_STORAGE_KEY = "stock-assistant-language-mode";
const PROFILE_ID_STORAGE_KEY = "stock-assistant-profile-id";

const ZH = {
  currentAlerts: "\u76ee\u524d\u63d0\u793a",
  noAlerts: "\u76ee\u524d\u6c92\u6709\u65b0\u7684\u63d0\u793a\u3002",
  loading: "\u8f09\u5165\u4e2d...",
  suppressedPrefix: "\u5df2\u7565\u904e",
  suppressedSuffix: "\u500b\u91cd\u8907\u63d0\u793a\u3002",
  dashboard: "\u5100\u8868\u677f",
  dashboardIntro: "\u7531 FastAPI \u5f8c\u7aef\u63d0\u4f9b\u7684\u5171\u7528\u500b\u4eba\u8a2d\u5b9a\u6aa2\u8996\u3002",
  ticker: "\u80a1\u7968\u4ee3\u865f",
  refresh: "\u91cd\u65b0\u6574\u7406",
  tickerDetail: "\u80a1\u7968\u8a73\u60c5",
  latestClose: "\u6700\u65b0\u6536\u5e02\u50f9",
  score: "\u8a55\u5206",
  label: "\u6a19\u7c64",
  actionSummary: "\u64cd\u4f5c\u6458\u8981",
  benchmarkStrength: "\u57fa\u6e96\u76f8\u5c0d\u5f37\u5ea6",
  explanation: "\u89e3\u91cb",
  forecast: "\u5c55\u671b",
  scenarioOnly: "\u53ea\u5c6c\u60c5\u666f\u5206\u6790\uff0c\u4e26\u975e\u4fdd\u8b49\u9810\u6e2c\u3002",
  trendRegime: "\u8da8\u52e2\u72c0\u614b",
  outlook5d: "5 \u65e5\u5c55\u671b",
  outlook20d: "20 \u65e5\u5c55\u671b",
  expectedRange: "\u9810\u671f\u5340\u9593",
  support: "\u652f\u6490\u4f4d",
  resistance: "\u963b\u529b\u4f4d",
  confidenceScore: "\u4fe1\u5fc3\u8a55\u5206",
  priceAndSma: "\u50f9\u683c\u8207 SMA",
  close: "\u6536\u5e02\u50f9",
  scoreOverTime: "\u8a55\u5206\u8d70\u52e2",
  totalScore: "\u7e3d\u8a55\u5206",
  settings: "\u8a2d\u5b9a",
  glossary: "\u8a5e\u5f59\u8868",
  language: "\u8a9e\u8a00",
  chinese: "\u4e2d\u6587",
};

function normalizePath(pathname) {
  if (pathname === GLOSSARY_PATH) return GLOSSARY_PATH;
  if (pathname === SETTINGS_PATH) return SETTINGS_PATH;
  return DASHBOARD_PATH;
}

function getInitialProfileId() {
  return window.localStorage.getItem(PROFILE_ID_STORAGE_KEY) || "demo-user";
}

function getInitialLanguageMode() {
  const saved = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  return saved === "en" || saved === "zh" || saved === "both" ? saved : "both";
}

function profileLanguageToMode(language) {
  if (language === "en" || language === "zh") return language;
  return "both";
}

function modeToProfileLanguage(mode) {
  if (mode === "en" || mode === "zh") return mode;
  return "bilingual";
}

function toNumeric(value) {
  if (value === null || value === undefined) return Number.NaN;
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

function getActionSummaryByMode(analyzeData, mode) {
  if (!analyzeData) return "";
  if (mode === "zh") return analyzeData.action_summary_zh || analyzeData.action_summary;
  if (mode === "both") return analyzeData.action_summary_bilingual || analyzeData.action_summary;
  return analyzeData.action_summary_en || analyzeData.action_summary;
}

function getExplanationBulletsByMode(analyzeData, mode) {
  if (!analyzeData) return [];
  if (mode === "zh") return analyzeData.explanation_bullets_zh || analyzeData.explanation_bullets || [];
  if (mode === "both") {
    return analyzeData.explanation_bullets_bilingual || analyzeData.explanation_bullets || [];
  }
  return analyzeData.explanation_bullets_en || analyzeData.explanation_bullets || [];
}

function formatBilingualLabel(mode, en, zh) {
  if (mode === "zh") return zh;
  if (mode === "en") return en;
  return `${en} / ${zh}`;
}

function CurrentAlertsPanel({ languageMode, alertScan, isLoading }) {
  const title = formatBilingualLabel(languageMode, "Current Alerts", ZH.currentAlerts);
  const noAlerts = formatBilingualLabel(languageMode, "No new alerts right now.", ZH.noAlerts);

  function formatAlertMessage(item) {
    if (languageMode === "zh") return item.message_zh;
    if (languageMode === "both") return `${item.message_en} / ${item.message_zh}`;
    return item.message_en;
  }

  return (
    <section className="panel">
      <h3>{title}</h3>
      {isLoading ? <p>{formatBilingualLabel(languageMode, "Loading...", ZH.loading)}</p> : null}
      {!isLoading && (!alertScan || !alertScan.alerts.length) ? <p>{noAlerts}</p> : null}
      {!isLoading && alertScan?.alerts?.length ? (
        <ul className="bullet-list">
          {alertScan.alerts.map((item) => (
            <li key={`${item.ticker}-${item.rule}`}>{formatAlertMessage(item)}</li>
          ))}
        </ul>
      ) : null}
      {!isLoading && alertScan?.suppressed_count ? (
        <p className="helper-text">
          {formatBilingualLabel(
            languageMode,
            `${alertScan.suppressed_count} repeated alerts were suppressed.`,
            `${ZH.suppressedPrefix} ${alertScan.suppressed_count} ${ZH.suppressedSuffix}`
          )}
        </p>
      ) : null}
    </section>
  );
}

function DashboardPage({ languageMode, profileId, currentWatchlist, onProfileUpdated }) {
  const [watchlistRows, setWatchlistRows] = useState([]);
  const [selectedTicker, setSelectedTicker] = useState("");
  const [analyzeData, setAnalyzeData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [alertScan, setAlertScan] = useState(null);
  const [isLoadingWatchlist, setIsLoadingWatchlist] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [isLoadingAlerts, setIsLoadingAlerts] = useState(false);
  const [error, setError] = useState("");

  async function loadWatchlist() {
    if (!currentWatchlist.length) {
      setWatchlistRows([]);
      setSelectedTicker("");
      return;
    }

    setIsLoadingWatchlist(true);
    setError("");
    try {
      const response = await fetchWatchlistAnalyze(currentWatchlist, DEFAULT_PERIOD);
      const rankedRows = response.ranked_results || [];
      setWatchlistRows(rankedRows);
      if (rankedRows.length > 0) {
        const tickers = rankedRows.map((row) => row.ticker);
        setSelectedTicker((currentTicker) => (tickers.includes(currentTicker) ? currentTicker : tickers[0]));
      }
    } catch (requestError) {
      setError(requestError.message || "Failed to load watchlist.");
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
    } catch (requestError) {
      setError(requestError.message || "Failed to load ticker detail.");
    } finally {
      setIsLoadingDetail(false);
    }
  }

  async function loadAlerts() {
    setIsLoadingAlerts(true);
    try {
      const payload = await fetchUserAlertScan(profileId);
      setAlertScan(payload);
    } catch {
      setAlertScan(null);
    } finally {
      setIsLoadingAlerts(false);
    }
  }

  useEffect(() => {
    loadWatchlist();
    loadAlerts();
  }, [currentWatchlist.join(","), profileId]);

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

  const explanationBullets = useMemo(
    () => getExplanationBulletsByMode(analyzeData, languageMode),
    [analyzeData, languageMode]
  );

  const actionSummaryDisplay = useMemo(
    () => getActionSummaryByMode(analyzeData, languageMode),
    [analyzeData, languageMode]
  );

  return (
    <>
      <header className="app-header">
        <div>
          <h1>{formatBilingualLabel(languageMode, "Dashboard", ZH.dashboard)}</h1>
          <p>
            {formatBilingualLabel(
              languageMode,
              "Shared profile view powered by the FastAPI backend.",
              ZH.dashboardIntro
            )}
          </p>
        </div>
        <div className="header-controls">
          <label htmlFor="ticker-select">{formatBilingualLabel(languageMode, "Ticker", ZH.ticker)}</label>
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
            {isLoadingWatchlist
              ? `${formatBilingualLabel(languageMode, "Refresh", ZH.refresh)}...`
              : formatBilingualLabel(languageMode, "Refresh", ZH.refresh)}
          </button>
        </div>
      </header>

      {error ? <p className="error-box">{error}</p> : null}

      <div className="layout-grid">
        <div>
          <WatchlistTable
            rows={watchlistRows}
            selectedTicker={selectedTicker}
            onSelectTicker={setSelectedTicker}
            languageMode={languageMode}
          />
          <WatchlistManager
            userId={profileId}
            watchlist={currentWatchlist}
            languageMode={languageMode}
            onUpdated={() => onProfileUpdated(profileId)}
          />
          <CurrentAlertsPanel
            languageMode={languageMode}
            alertScan={alertScan}
            isLoading={isLoadingAlerts}
          />
        </div>

        <section className="panel">
          <h3>{formatBilingualLabel(languageMode, "Ticker Detail", ZH.tickerDetail)}</h3>
          {isLoadingDetail || !analyzeData ? (
            <p>{formatBilingualLabel(languageMode, "Loading...", ZH.loading)}</p>
          ) : (
            <>
              <div className="detail-grid">
                <p>
                  <strong>{formatBilingualLabel(languageMode, "Ticker", ZH.ticker)}:</strong> {analyzeData.ticker}
                </p>
                <p>
                  <strong>{formatBilingualLabel(languageMode, "Latest Close", ZH.latestClose)}:</strong>{" "}
                  {analyzeData.latest_close.toFixed(2)}
                </p>
                <p>
                  <strong>{formatBilingualLabel(languageMode, "Score", ZH.score)}:</strong>{" "}
                  {analyzeData.score_breakdown.total_score}
                </p>
                <p>
                  <strong>{formatBilingualLabel(languageMode, "Label", ZH.label)}:</strong> {analyzeData.label}
                </p>
                <p>
                  <strong>{formatBilingualLabel(languageMode, "Action Summary", ZH.actionSummary)}:</strong>{" "}
                  {actionSummaryDisplay}
                </p>
                <p>
                  <strong>{formatBilingualLabel(languageMode, "Benchmark Strength", ZH.benchmarkStrength)}:</strong>{" "}
                  {analyzeData.benchmark_relative?.benchmark_strength_score ?? "N/A"}
                </p>
              </div>
              <h4>{formatBilingualLabel(languageMode, "Explanation", ZH.explanation)}</h4>
              <ul className="bullet-list">
                {explanationBullets.map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>
              <section className="forecast-card">
                <h4>{formatBilingualLabel(languageMode, "Forecast", ZH.forecast)}</h4>
                <p className="helper-text">
                  {formatBilingualLabel(
                    languageMode,
                    "Scenario-based forecast only.",
                    ZH.scenarioOnly
                  )}
                </p>
                {!forecastData ? (
                  <p>{formatBilingualLabel(languageMode, "Loading...", ZH.loading)}</p>
                ) : (
                  <div className="forecast-grid">
                    <p>
                      <strong>{formatBilingualLabel(languageMode, "Trend Regime", ZH.trendRegime)}:</strong>{" "}
                      {forecastData.trend_regime_en} / {forecastData.trend_regime_zh}
                    </p>
                    <p>
                      <strong>{formatBilingualLabel(languageMode, "5-Day Outlook", ZH.outlook5d)}:</strong>{" "}
                      {forecastData.outlook_5d}
                    </p>
                    <p>
                      <strong>{formatBilingualLabel(languageMode, "20-Day Outlook", ZH.outlook20d)}:</strong>{" "}
                      {forecastData.outlook_20d}
                    </p>
                    <p>
                      <strong>{formatBilingualLabel(languageMode, "Expected Range", ZH.expectedRange)}:</strong>{" "}
                      {forecastData.expected_range?.lower?.toFixed(2)} - {forecastData.expected_range?.upper?.toFixed(2)}
                    </p>
                    <p>
                      <strong>{formatBilingualLabel(languageMode, "Support", ZH.support)}:</strong>{" "}
                      {forecastData.levels?.support_level?.toFixed(2)}
                    </p>
                    <p>
                      <strong>{formatBilingualLabel(languageMode, "Resistance", ZH.resistance)}:</strong>{" "}
                      {forecastData.levels?.resistance_level?.toFixed(2)}
                    </p>
                    <p>
                      <strong>{formatBilingualLabel(languageMode, "Confidence Score", ZH.confidenceScore)}:</strong>{" "}
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
        title={formatBilingualLabel(languageMode, "Price and SMA", ZH.priceAndSma)}
        points={chartSeries}
        overlays={{
          horizontalLines: [
            {
              key: "support",
              label: formatBilingualLabel(languageMode, "Support", ZH.support),
              value: toNumeric(forecastData?.levels?.support_level),
              color: "#0f766e",
            },
            {
              key: "resistance",
              label: formatBilingualLabel(languageMode, "Resistance", ZH.resistance),
              value: toNumeric(forecastData?.levels?.resistance_level),
              color: "#b45309",
            },
          ],
          rangeBand:
            forecastData && forecastData.expected_range
              ? {
                  key: "expected-range",
                  label: formatBilingualLabel(languageMode, "Expected Range", ZH.expectedRange),
                  lower: toNumeric(forecastData.expected_range.lower),
                  upper: toNumeric(forecastData.expected_range.upper),
                  color: "#2563eb",
                }
              : null,
        }}
        lines={[
          { key: "close", label: formatBilingualLabel(languageMode, "Close", ZH.close), color: "#111827" },
          { key: "sma_20", label: "SMA20", color: "#2563eb" },
          { key: "sma_50", label: "SMA50", color: "#16a34a" },
          { key: "sma_200", label: "SMA200", color: "#d97706" },
        ]}
      />

      <div className="chart-grid">
        <LineChart
          title="RSI (14)"
          points={chartSeries}
          lines={[{ key: "rsi_14", label: "RSI14", color: "#7c3aed" }]}
          height={180}
        />
        <LineChart
          title="MACD"
          points={chartSeries}
          lines={[
            { key: "macd_line", label: "MACD", color: "#0f766e" },
            { key: "macd_signal", label: "Signal", color: "#dc2626" },
          ]}
          height={180}
        />
      </div>

      <LineChart
        title={formatBilingualLabel(languageMode, "Score Over Time", ZH.scoreOverTime)}
        points={scoreSeries}
        lines={[
          {
            key: "total_score",
            label: formatBilingualLabel(languageMode, "Total Score", ZH.totalScore),
            color: "#374151",
          },
        ]}
        height={180}
      />
    </>
  );
}

export default function App() {
  const [routePath, setRoutePath] = useState(() => normalizePath(window.location.pathname));
  const [profileId, setProfileId] = useState(getInitialProfileId);
  const [languageMode, setLanguageMode] = useState(getInitialLanguageMode);
  const [profile, setProfile] = useState(null);
  const [currentWatchlist, setCurrentWatchlist] = useState([]);
  const [profileError, setProfileError] = useState("");

  useEffect(() => {
    const onPopState = () => setRoutePath(normalizePath(window.location.pathname));
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, languageMode);
  }, [languageMode]);

  useEffect(() => {
    window.localStorage.setItem(PROFILE_ID_STORAGE_KEY, profileId);
  }, [profileId]);

  async function loadSharedProfile(nextProfileId = profileId) {
    setProfileError("");
    try {
      const [nextProfile, watchlistResponse] = await Promise.all([
        fetchUserProfile(nextProfileId),
        fetchUserWatchlist(nextProfileId),
      ]);
      setProfile(nextProfile);
      setCurrentWatchlist(watchlistResponse.watchlist || []);
      setLanguageMode(profileLanguageToMode(nextProfile.preferred_language));
    } catch (requestError) {
      setProfileError(requestError.message || "Failed to load shared profile.");
    }
  }

  useEffect(() => {
    loadSharedProfile(profileId);
  }, [profileId]);

  async function handleProfileIdChange(nextProfileId) {
    const cleanId = nextProfileId.trim() || "demo-user";
    setProfileId(cleanId);
  }

  async function handleLanguageChange(nextMode) {
    setLanguageMode(nextMode);
    try {
      await updateUserProfileSettings({
        user_id: profileId,
        preferred_language: modeToProfileLanguage(nextMode),
        last_active_source: "dashboard",
      });
      await loadSharedProfile(profileId);
    } catch (requestError) {
      setProfileError(requestError.message || "Failed to update language.");
    }
  }

  return (
    <main className="app-shell">
      <header className="panel global-header">
        <nav className="top-nav">
          <button
            type="button"
            className={routePath === DASHBOARD_PATH ? "nav-link active" : "nav-link"}
            onClick={() => navigateTo(DASHBOARD_PATH, setRoutePath)}
          >
            {formatBilingualLabel(languageMode, "Dashboard", ZH.dashboard)}
          </button>
          <button
            type="button"
            className={routePath === SETTINGS_PATH ? "nav-link active" : "nav-link"}
            onClick={() => navigateTo(SETTINGS_PATH, setRoutePath)}
          >
            {formatBilingualLabel(languageMode, "Settings", ZH.settings)}
          </button>
          <button
            type="button"
            className={routePath === GLOSSARY_PATH ? "nav-link active" : "nav-link"}
            onClick={() => navigateTo(GLOSSARY_PATH, setRoutePath)}
          >
            {formatBilingualLabel(languageMode, "Glossary", ZH.glossary)}
          </button>
        </nav>
        <div className="header-controls">
          <label htmlFor="global-lang-select">{formatBilingualLabel(languageMode, "Language", ZH.language)}</label>
          <select
            id="global-lang-select"
            value={languageMode}
            onChange={(event) => handleLanguageChange(event.target.value)}
          >
            <option value="en">English</option>
            <option value="zh">{ZH.chinese}</option>
            <option value="both">English + {ZH.chinese}</option>
          </select>
        </div>
      </header>

      {profileError ? <p className="error-box">{profileError}</p> : null}

      {routePath === GLOSSARY_PATH ? (
        <GlossaryPage languageMode={languageMode} />
      ) : routePath === SETTINGS_PATH ? (
        <SettingsPage
          profileId={profileId}
          onProfileIdChange={handleProfileIdChange}
          profile={profile}
          languageMode={languageMode}
          onProfileUpdated={loadSharedProfile}
          currentWatchlist={currentWatchlist}
        />
      ) : (
        <DashboardPage
          languageMode={languageMode}
          profileId={profileId}
          currentWatchlist={currentWatchlist}
          onProfileUpdated={loadSharedProfile}
        />
      )}
    </main>
  );
}
