import React, { useEffect, useMemo, useState } from "react";

import {
  fetchModelAccuracy,
  fetchModelHistory,
  fetchModelLatest,
} from "../api";
import LineChart from "../components/LineChart";

const DEFAULT_PERIOD = "5y";
const DEFAULT_TARGET = "target_5d_updown";
const DEFAULT_MODEL = "logistic_regression";

const ZH = {
  title: "模型評估",
  intro: "查看模型訊號、命中率，以及最新預測與實際結果。",
  ticker: "股票代號",
  latestPrediction: "最新預測",
  predictedSignal: "預測訊號",
  confidence: "信心",
  actualOutcome: "實際結果",
  hitMiss: "命中 / 失誤",
  rollingAccuracy: "滾動命中率",
  modelMetrics: "模型指標",
  latestVsActual: "最新預測對比實際結果",
  predictionChart: "預測 / 信心 / 實際結果",
  technicalState: "技術狀態",
  newsSentiment: "新聞情緒",
  benchmarkStrength: "相對基準強度",
  explanation: "解釋",
  loading: "載入中...",
  noData: "未有已儲存的模型結果。請先執行訓練。",
  predictedValue: "預測值",
  actualValue: "實際值",
  confidenceLine: "信心線",
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

export default function ModelEvaluationPage({ languageMode, currentWatchlist }) {
  const [selectedTicker, setSelectedTicker] = useState(currentWatchlist[0] || "VOO");
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
    if (!selectedTicker) return;

    let isActive = true;
    async function loadModelViews() {
      setIsLoading(true);
      setError("");
      try {
        const [latest, history, accuracy] = await Promise.all([
          fetchModelLatest(selectedTicker, DEFAULT_PERIOD, DEFAULT_TARGET, DEFAULT_MODEL),
          fetchModelHistory(selectedTicker, DEFAULT_PERIOD, DEFAULT_TARGET, DEFAULT_MODEL, 180),
          fetchModelAccuracy(selectedTicker, DEFAULT_PERIOD, DEFAULT_TARGET, DEFAULT_MODEL, 20),
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
  }, [selectedTicker]);

  const predictionSeries = useMemo(() => {
    if (!historyData?.history) return [];
    return historyData.history.map((item) => ({
      date: item.prediction_date,
      predicted_value: toNumeric(item.predicted_value),
      actual_future_result: toNumeric(item.actual_future_result),
      confidence_score: toNumeric(item.confidence_score),
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
          <p>{labelByMode(languageMode, "Review model signals, hit rate, and latest predicted vs actual outcomes.", ZH.intro)}</p>
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
              <p className="helper-text">
                {accuracyData?.metrics_summary?.validation_note}
              </p>
            </section>
          </div>

          <LineChart
            title={labelByMode(languageMode, "Prediction / Confidence / Actual Result", ZH.predictionChart)}
            points={predictionSeries}
            lines={[
              {
                key: "predicted_value",
                label: labelByMode(languageMode, "Predicted Value", ZH.predictedValue),
                color: "#1d4ed8",
              },
              {
                key: "actual_future_result",
                label: labelByMode(languageMode, "Actual Value", ZH.actualValue),
                color: "#047857",
              },
              {
                key: "confidence_score",
                label: labelByMode(languageMode, "Confidence", ZH.confidenceLine),
                color: "#b45309",
              },
            ]}
          />

          <LineChart
            title={labelByMode(languageMode, "Rolling Hit Rate", ZH.rollingAccuracy)}
            points={rollingAccuracySeries}
            lines={[
              {
                key: "rolling_accuracy",
                label: labelByMode(languageMode, "Rolling Hit Rate", ZH.rollingAccuracy),
                color: "#374151",
              },
            ]}
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
            <h3>{labelByMode(languageMode, "Recent Prediction History", "最近預測紀錄")}</h3>
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
