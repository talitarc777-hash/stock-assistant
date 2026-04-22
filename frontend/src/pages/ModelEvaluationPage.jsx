import React, { useEffect, useMemo, useState } from "react";

import {
  fetchModelAccuracy,
  fetchModelHistory,
  fetchModelLatest,
} from "../api";
import LineChart from "../components/LineChart";
import PredictionChart from "../components/PredictionChart";
import {
  labelByMode,
  MODEL_EVALUATION_LABELS as L,
} from "../i18n/bilingualUiLabels";
import { fetchModelEvaluationSettings } from "../services/modelSettingsApi";

const DEFAULT_PERIOD = "5y";
const DEFAULT_TARGET = "target_5d_updown";
const DEFAULT_MODEL = "logistic_regression";

function toNumeric(value) {
  if (value === null || value === undefined) return Number.NaN;
  const num = Number(value);
  return Number.isFinite(num) ? num : Number.NaN;
}

function formatMetricValue(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "N/A";
  return Number(value).toFixed(3);
}

export default function ModelEvaluationPage({ languageMode, currentWatchlist, profileId }) {
  const [selectedTicker, setSelectedTicker] = useState(currentWatchlist[0] || "VOO");
  const [selectedModelName, setSelectedModelName] = useState(DEFAULT_MODEL);
  const [latestData, setLatestData] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [accuracyData, setAccuracyData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [loadState, setLoadState] = useState("idle");
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    if (!currentWatchlist.length) return;
    if (!currentWatchlist.includes(selectedTicker)) {
      setSelectedTicker(currentWatchlist[0]);
    }
  }, [currentWatchlist.join(","), selectedTicker]);

  useEffect(() => {
    let isActive = true;
    async function loadModelSettings() {
      try {
        const settings = await fetchModelEvaluationSettings(profileId);
        if (!isActive) return;
        setSelectedModelName(settings.selected_model_name || DEFAULT_MODEL);
      } catch {
        if (!isActive) return;
        setSelectedModelName(DEFAULT_MODEL);
      }
    }
    if (profileId) {
      loadModelSettings();
    }
    return () => {
      isActive = false;
    };
  }, [profileId]);

  useEffect(() => {
    if (!selectedTicker) return;

    let isActive = true;
    async function loadModelViews() {
      setLatestData(null);
      setHistoryData(null);
      setAccuracyData(null);
      setLoadState("loading");
      setIsLoading(true);
      setError("");
      try {
        const [latest, history, accuracy] = await Promise.allSettled([
          fetchModelLatest(selectedTicker, DEFAULT_PERIOD, DEFAULT_TARGET, selectedModelName, profileId),
          fetchModelHistory(selectedTicker, DEFAULT_PERIOD, DEFAULT_TARGET, selectedModelName, 180, profileId),
          fetchModelAccuracy(selectedTicker, DEFAULT_PERIOD, DEFAULT_TARGET, selectedModelName, 20, profileId),
        ]);
        if (!isActive) return;
        setLatestData(latest.status === "fulfilled" ? latest.value : null);
        setHistoryData(history.status === "fulfilled" ? history.value : null);
        setAccuracyData(accuracy.status === "fulfilled" ? accuracy.value : null);
        const failedCount = [latest, history, accuracy].filter((item) => item.status === "rejected").length;
        setLoadState(failedCount > 0 ? (failedCount === 3 ? "failed" : "partial") : "ready");
        if (failedCount > 0) {
          setError(
            failedCount === 3
              ? "We could not load model evaluation right now. Please retry in a moment."
              : "Some model evaluation sections are still loading or unavailable."
          );
        }
      } catch (requestError) {
        if (!isActive) return;
        setLatestData(null);
        setHistoryData(null);
        setAccuracyData(null);
        setLoadState("failed");
        setError(requestError.message || "Failed to load model evaluation.");
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    loadModelViews();
    return () => {
      isActive = false;
    };
  }, [selectedTicker, selectedModelName, profileId, refreshToken]);

  const predictionSeries = useMemo(() => {
    if (!historyData?.history) return [];
    return historyData.history.map((item) => ({
      date: item.prediction_date,
      predicted_value: toNumeric(item.predicted_value) * 100,
      actual_future_result: toNumeric(item.actual_future_result) * 100,
      confidence_score: toNumeric(item.confidence_score) * 100,
    }));
  }, [historyData]);

  const rollingAccuracySeries = useMemo(() => {
    if (!accuracyData?.rolling_accuracy) return [];
    return accuracyData.rolling_accuracy.map((item) => ({
      date: item.date,
      rolling_accuracy: toNumeric(item.rolling_accuracy),
    }));
  }, [accuracyData]);

  const latestPrediction = latestData?.latest_prediction || null;
  const metricValues = accuracyData?.metrics_summary?.metrics || {};

  return (
    <>
      <header className="app-header">
        <div>
          <h1>{labelByMode(languageMode, L.title.en, L.title.zh)}</h1>
          <p>
            {labelByMode(
              languageMode,
              L.intro.en,
              L.intro.zh
            )}
          </p>
        </div>
        <div className="header-controls">
          <label htmlFor="model-ticker-select">{labelByMode(languageMode, L.ticker.en, L.ticker.zh)}</label>
          <select
            id="model-ticker-select"
            value={selectedTicker}
            onChange={(event) => setSelectedTicker(event.target.value)}
          >
            {(currentWatchlist.length ? currentWatchlist : ["VOO"]).map((ticker) => (
              <option key={ticker} value={ticker}>
                {ticker}
              </option>
            ))}
          </select>
          <span className="helper-chip">
            {labelByMode(languageMode, L.model.en, L.model.zh)}: {selectedModelName}
          </span>
        </div>
      </header>

      {error ? (
        <div className="error-box">
          <p>{error}</p>
          <button type="button" onClick={() => setRefreshToken((value) => value + 1)}>
            {labelByMode(languageMode, "Retry model data", "重新整理模型資料")}
          </button>
        </div>
      ) : null}
      {isLoading ? (
        <section className="panel">
          <p>{labelByMode(languageMode, "Loading model evaluation. Individual sections will appear as they finish.", "正在載入模型評估，完成的區塊會先顯示。")}</p>
        </section>
      ) : null}
      {!isLoading && !latestPrediction && !error ? <p className="panel">{labelByMode(languageMode, L.noData.en, L.noData.zh)}</p> : null}

      {latestPrediction ? (
        <>
          <div className="layout-grid">
            <section className="panel">
              <h3>{labelByMode(languageMode, L.latestPrediction.en, L.latestPrediction.zh)}</h3>
              <div className="detail-grid">
                <p>
                  <strong>{labelByMode(languageMode, L.predictedSignal.en, L.predictedSignal.zh)}:</strong>{" "}
                  {String(latestPrediction.predicted_value)}
                </p>
                <p>
                  <strong>{labelByMode(languageMode, L.confidence.en, L.confidence.zh)}:</strong>{" "}
                  {latestPrediction.confidence_score !== null && latestPrediction.confidence_score !== undefined
                    ? `${(Number(latestPrediction.confidence_score) * 100).toFixed(0)}%`
                    : "N/A"}
                </p>
                <p>
                  <strong>{labelByMode(languageMode, L.actualOutcome.en, L.actualOutcome.zh)}:</strong>{" "}
                  {String(latestPrediction.actual_future_result)}
                </p>
                <p>
                  <strong>{labelByMode(languageMode, L.hitMiss.en, L.hitMiss.zh)}:</strong> {latestPrediction.hit_miss}
                </p>
              </div>
              <h4>{labelByMode(languageMode, L.latestVsActual.en, L.latestVsActual.zh)}</h4>
              <p className="helper-text">{latestPrediction.explanation}</p>
            </section>

            <section className="panel">
              <h3>{labelByMode(languageMode, L.modelMetrics.en, L.modelMetrics.zh)}</h3>
              <div className="detail-grid">
                <p><strong>Accuracy:</strong> {formatMetricValue(metricValues.accuracy)}</p>
                <p><strong>Precision:</strong> {formatMetricValue(metricValues.precision)}</p>
                <p><strong>Recall:</strong> {formatMetricValue(metricValues.recall)}</p>
                <p><strong>F1:</strong> {formatMetricValue(metricValues.f1)}</p>
                <p><strong>MAE:</strong> {formatMetricValue(metricValues.mae)}</p>
                <p><strong>RMSE:</strong> {formatMetricValue(metricValues.rmse)}</p>
              </div>
              <p className="helper-text">{accuracyData?.metrics_summary?.validation_note}</p>
            </section>
          </div>

          <PredictionChart
            ticker={selectedTicker}
            points={predictionSeries}
            languageMode={languageMode}
          />

          <LineChart
            title={labelByMode(languageMode, L.rollingAccuracy.en, L.rollingAccuracy.zh)}
            subtitle={`Ticker: ${selectedTicker} | Last 6 Months`}
            points={rollingAccuracySeries}
            xAxisLabel="Date"
            yAxisLabel="Score"
            yValueKind="score"
            lines={[
              {
                key: "rolling_accuracy",
                label: labelByMode(languageMode, L.rollingAccuracy.en, L.rollingAccuracy.zh),
                color: "#374151",
                strokeWidth: 2.4,
                valueKind: "score",
              },
            ]}
            noDataMessage={labelByMode(languageMode, L.noChartData.en, L.noChartData.zh)}
            height={180}
          />

          <LineChart
            title={labelByMode(languageMode, L.predictionConfidence.en, L.predictionConfidence.zh)}
            subtitle={`Ticker: ${selectedTicker} | Last 6 Months`}
            points={predictionSeries}
            xAxisLabel="Date"
            yAxisLabel="Confidence (%)"
            yValueKind="percent"
            lines={[
              {
                key: "confidence_score",
                label: labelByMode(languageMode, L.confidence.en, L.confidence.zh),
                color: "#1d4ed8",
                strokeWidth: 2.6,
                valueKind: "percent",
              },
            ]}
            noDataMessage={labelByMode(languageMode, L.noChartData.en, L.noChartData.zh)}
            height={180}
          />

          <div className="chart-grid">
            <section className="panel explanation-panel">
              <h3>{labelByMode(languageMode, L.technicalState.en, L.technicalState.zh)}</h3>
              <p>{latestPrediction.technical_state_summary}</p>
            </section>
            <section className="panel explanation-panel">
              <h3>{labelByMode(languageMode, L.newsSentiment.en, L.newsSentiment.zh)}</h3>
              <p>{latestPrediction.news_sentiment_summary}</p>
            </section>
          </div>

          <section className="panel explanation-panel">
            <h3>{labelByMode(languageMode, L.benchmarkStrength.en, L.benchmarkStrength.zh)}</h3>
            <p>{latestPrediction.benchmark_strength_summary}</p>
          </section>

          <section className="panel">
            <h3>{labelByMode(languageMode, L.recentHistory.en, L.recentHistory.zh)}</h3>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>{labelByMode(languageMode, L.predictedSignal.en, L.predictedSignal.zh)}</th>
                    <th>{labelByMode(languageMode, L.confidence.en, L.confidence.zh)}</th>
                    <th>{labelByMode(languageMode, L.actualOutcome.en, L.actualOutcome.zh)}</th>
                    <th>{labelByMode(languageMode, L.hitMiss.en, L.hitMiss.zh)}</th>
                  </tr>
                </thead>
                <tbody>
                  {(historyData?.history || []).slice(-20).reverse().map((item) => (
                    <tr key={`${item.prediction_date}-${item.evaluation_window}`}>
                      <td>{item.prediction_date}</td>
                      <td>{String(item.predicted_value)}</td>
                      <td>
                        {item.confidence_score !== null && item.confidence_score !== undefined
                          ? `${(Number(item.confidence_score) * 100).toFixed(0)}%`
                          : "N/A"}
                      </td>
                      <td>{String(item.actual_future_result)}</td>
                      <td>{item.hit_miss}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      ) : loadState === "partial" ? (
        <section className="panel">
          <p>
            {labelByMode(
              languageMode,
              "Partial model data loaded. Retry if you want the missing sections.",
              "部分模型資料已載入，如需補齊其餘區塊可按重試。"
            )}
          </p>
        </section>
      ) : null}
    </>
  );
}
