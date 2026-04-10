import React, { useEffect, useMemo, useState } from "react";

import {
  fetchModelAccuracy,
  fetchModelHistory,
  fetchModelLatest,
} from "../api";
import LineChart from "../components/LineChart";
import PredictionChart from "../components/PredictionChart";
import { fetchModelEvaluationSettings } from "../services/modelSettingsApi";

const DEFAULT_PERIOD = "5y";
const DEFAULT_TARGET = "target_5d_updown";
const DEFAULT_MODEL = "logistic_regression";

const ZH = {
  title: "\u6a21\u578b\u8a55\u4f30",
  intro: "\u67e5\u770b\u6a21\u578b\u8a0a\u865f\u3001\u547d\u4e2d\u7387\uff0c\u4ee5\u53ca\u6700\u65b0\u9810\u6e2c\u8207\u5be6\u969b\u7d50\u679c\u3002",
  ticker: "\u80a1\u7968\u4ee3\u865f",
  latestPrediction: "\u6700\u65b0\u9810\u6e2c",
  predictedSignal: "\u9810\u6e2c\u8a0a\u865f",
  confidence: "\u4fe1\u5fc3",
  actualOutcome: "\u5be6\u969b\u7d50\u679c",
  hitMiss: "\u547d\u4e2d / \u672a\u4e2d",
  rollingAccuracy: "\u6efe\u52d5\u547d\u4e2d\u7387",
  modelMetrics: "\u6a21\u578b\u6307\u6a19",
  latestVsActual: "\u6700\u65b0\u9810\u6e2c\u8207\u5be6\u969b\u6bd4\u8f03",
  technicalState: "\u6280\u8853\u72c0\u614b",
  newsSentiment: "\u65b0\u805e\u60c5\u7dd2",
  benchmarkStrength: "\u76f8\u5c0d\u57fa\u6e96\u5f37\u5f31",
  loading: "\u8f09\u5165\u4e2d...",
  noData: "\u66ab\u6642\u672a\u6709\u5df2\u5132\u5b58\u7684\u6a21\u578b\u7d50\u679c\uff0c\u8acb\u5148\u57f7\u884c\u8a13\u7df4\u3002",
  recentHistory: "\u6700\u8fd1\u9810\u6e2c\u7d00\u9304",
  predictionConfidence: "\u9810\u6e2c\u4fe1\u5fc3",
  model: "\u6a21\u578b",
  noChartData: "\u6c92\u6709\u53ef\u7528\u8cc7\u6599",
};

function labelByMode(mode, en, zh) {
  if (mode === "zh") return zh;
  if (mode === "en") return en;
  return `${en} / ${zh}`;
}

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
      setIsLoading(true);
      setError("");
      try {
        const [latest, history, accuracy] = await Promise.all([
          fetchModelLatest(selectedTicker, DEFAULT_PERIOD, DEFAULT_TARGET, selectedModelName, profileId),
          fetchModelHistory(selectedTicker, DEFAULT_PERIOD, DEFAULT_TARGET, selectedModelName, 180, profileId),
          fetchModelAccuracy(selectedTicker, DEFAULT_PERIOD, DEFAULT_TARGET, selectedModelName, 20, profileId),
        ]);
        if (!isActive) return;
        setLatestData(latest);
        setHistoryData(history);
        setAccuracyData(accuracy);
      } catch (requestError) {
        if (!isActive) return;
        setLatestData(null);
        setHistoryData(null);
        setAccuracyData(null);
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
  }, [selectedTicker, selectedModelName, profileId]);

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
          <h1>{labelByMode(languageMode, "Model Evaluation", ZH.title)}</h1>
          <p>
            {labelByMode(
              languageMode,
              "Review model signals, hit rate, and latest predicted vs actual outcomes.",
              ZH.intro
            )}
          </p>
        </div>
        <div className="header-controls">
          <label htmlFor="model-ticker-select">{labelByMode(languageMode, "Ticker", ZH.ticker)}</label>
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
            {labelByMode(languageMode, "Model", ZH.model)}: {selectedModelName}
          </span>
        </div>
      </header>

      {error ? <p className="error-box">{error}</p> : null}
      {isLoading ? <p className="panel">{labelByMode(languageMode, "Loading...", ZH.loading)}</p> : null}
      {!isLoading && !latestPrediction && !error ? (
        <p className="panel">{labelByMode(languageMode, "No saved model results yet. Run training first.", ZH.noData)}</p>
      ) : null}

      {latestPrediction ? (
        <>
          <div className="layout-grid">
            <section className="panel">
              <h3>{labelByMode(languageMode, "Latest Prediction", ZH.latestPrediction)}</h3>
              <div className="detail-grid">
                <p>
                  <strong>{labelByMode(languageMode, "Predicted signal", ZH.predictedSignal)}:</strong>{" "}
                  {String(latestPrediction.predicted_value)}
                </p>
                <p>
                  <strong>{labelByMode(languageMode, "Confidence", ZH.confidence)}:</strong>{" "}
                  {latestPrediction.confidence_score !== null && latestPrediction.confidence_score !== undefined
                    ? `${(Number(latestPrediction.confidence_score) * 100).toFixed(0)}%`
                    : "N/A"}
                </p>
                <p>
                  <strong>{labelByMode(languageMode, "Actual outcome", ZH.actualOutcome)}:</strong>{" "}
                  {String(latestPrediction.actual_future_result)}
                </p>
                <p>
                  <strong>{labelByMode(languageMode, "Hit / miss", ZH.hitMiss)}:</strong> {latestPrediction.hit_miss}
                </p>
              </div>
              <h4>{labelByMode(languageMode, "Latest forecast vs actual", ZH.latestVsActual)}</h4>
              <p className="helper-text">{latestPrediction.explanation}</p>
            </section>

            <section className="panel">
              <h3>{labelByMode(languageMode, "Model Metrics", ZH.modelMetrics)}</h3>
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
            title={labelByMode(languageMode, "Rolling Hit Rate", ZH.rollingAccuracy)}
            subtitle={`Ticker: ${selectedTicker} | Last 6 Months`}
            points={rollingAccuracySeries}
            xAxisLabel="Date"
            yAxisLabel="Score"
            yValueKind="score"
            lines={[
              {
                key: "rolling_accuracy",
                label: labelByMode(languageMode, "Rolling Hit Rate", ZH.rollingAccuracy),
                color: "#374151",
                strokeWidth: 2.4,
                valueKind: "score",
              },
            ]}
            noDataMessage={labelByMode(languageMode, "No data available", ZH.noChartData)}
            height={180}
          />

          <LineChart
            title={labelByMode(languageMode, "Prediction Confidence", ZH.predictionConfidence)}
            subtitle={`Ticker: ${selectedTicker} | Last 6 Months`}
            points={predictionSeries}
            xAxisLabel="Date"
            yAxisLabel="Confidence (%)"
            yValueKind="percent"
            lines={[
              {
                key: "confidence_score",
                label: labelByMode(languageMode, "Confidence", ZH.confidence),
                color: "#1d4ed8",
                strokeWidth: 2.6,
                valueKind: "percent",
              },
            ]}
            noDataMessage={labelByMode(languageMode, "No data available", ZH.noChartData)}
            height={180}
          />

          <div className="chart-grid">
            <section className="panel explanation-panel">
              <h3>{labelByMode(languageMode, "Technical State", ZH.technicalState)}</h3>
              <p>{latestPrediction.technical_state_summary}</p>
            </section>
            <section className="panel explanation-panel">
              <h3>{labelByMode(languageMode, "News Sentiment", ZH.newsSentiment)}</h3>
              <p>{latestPrediction.news_sentiment_summary}</p>
            </section>
          </div>

          <section className="panel explanation-panel">
            <h3>{labelByMode(languageMode, "Benchmark Strength", ZH.benchmarkStrength)}</h3>
            <p>{latestPrediction.benchmark_strength_summary}</p>
          </section>

          <section className="panel">
            <h3>{labelByMode(languageMode, "Recent Prediction History", ZH.recentHistory)}</h3>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>{labelByMode(languageMode, "Predicted signal", ZH.predictedSignal)}</th>
                    <th>{labelByMode(languageMode, "Confidence", ZH.confidence)}</th>
                    <th>{labelByMode(languageMode, "Actual outcome", ZH.actualOutcome)}</th>
                    <th>{labelByMode(languageMode, "Hit / miss", ZH.hitMiss)}</th>
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
      ) : null}
    </>
  );
}
