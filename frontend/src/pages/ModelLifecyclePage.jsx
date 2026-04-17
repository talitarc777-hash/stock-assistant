import React, { useEffect, useState } from "react";

import {
  fetchModelLifecycleRegistry,
  fetchModelLifecycleRuns,
  fetchModelLifecycleStatus,
  runModelLifecycleNow,
} from "../api";

function labelByMode(mode, en, zh) {
  if (mode === "zh") return zh;
  if (mode === "en") return en;
  return `${en} / ${zh}`;
}

function scoreText(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "N/A";
  return n.toFixed(3);
}

const ZH = {
  title: "\u6a21\u578b\u751f\u547d\u9031\u671f",
  intro: "\u7cfb\u7d71\u6703\u81ea\u52d5\u91cd\u8a13\u3001\u9a57\u8b49\u8207\u5347\u7d1a\u6a21\u578b\uff0c\u6e1b\u5c11\u624b\u52d5\u9010\u4e00\u6e96\u5099\u6a21\u578b\u7684\u9700\u8981\u3002",
  loading: "\u8f09\u5165\u4e2d...",
  refresh: "\u91cd\u65b0\u6574\u7406",
  runNow: "\u7acb\u5373\u57f7\u884c",
  running: "\u57f7\u884c\u4e2d...",
  status: "\u751f\u547d\u9031\u671f\u72c0\u614b",
  scheduler: "\u6392\u7a0b\u5668",
  cadence: "\u6aa2\u67e5\u9593\u9694",
  lastRun: "\u4e0a\u6b21\u6392\u7a0b\u6aa2\u67e5",
  nextRun: "\u4e0b\u6b21\u6392\u7a0b\u6aa2\u67e5",
  lastRetrain: "\u4e0a\u6b21\u91cd\u8a13\u6642\u9593",
  nextRetrain: "\u4e0b\u6b21\u9810\u8a08\u91cd\u8a13",
  lastWorkflow: "\u6700\u8fd1\u6d41\u7a0b\u985e\u578b",
  production: "\u76ee\u524d\u751f\u7522\u6a21\u578b",
  metrics: "\u6700\u8fd1\u8a55\u4f30\u6307\u6a19",
  triggers: "\u89f8\u767c\u689d\u4ef6",
  noTriggers: "\u76ee\u524d\u6c92\u6709\u555f\u52d5\u4e2d\u7684\u91cd\u8a13\u89f8\u767c\u689d\u4ef6\u3002",
  registry: "\u6a21\u578b\u767b\u8a18\u8868",
  runs: "\u6700\u8fd1\u5de5\u4f5c\u6d41\u7a0b\u8a18\u9304",
  workflow: "\u6d41\u7a0b",
  reason: "\u539f\u56e0",
  result: "\u7d50\u679c",
};

export default function ModelLifecyclePage({ languageMode }) {
  const [status, setStatus] = useState(null);
  const [registry, setRegistry] = useState([]);
  const [runs, setRuns] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRunningNow, setIsRunningNow] = useState(false);
  const [error, setError] = useState("");

  async function loadAll() {
    setIsLoading(true);
    setError("");
    try {
      const [statusPayload, registryPayload, runsPayload] = await Promise.all([
        fetchModelLifecycleStatus("VOO", "5y", "target_5d_updown", 8),
        fetchModelLifecycleRegistry(60),
        fetchModelLifecycleRuns(12),
      ]);
      setStatus(statusPayload);
      setRegistry(registryPayload || []);
      setRuns(runsPayload || []);
    } catch (requestError) {
      setError(requestError.message || "Failed to load model lifecycle status.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  async function handleRunNow() {
    setIsRunningNow(true);
    setError("");
    try {
      await runModelLifecycleNow("daily_incremental", "manual_dashboard_run");
      await loadAll();
    } catch (requestError) {
      setError(requestError.message || "Failed to trigger lifecycle run.");
    } finally {
      setIsRunningNow(false);
    }
  }

  const production = status?.production_model || null;

  return (
    <>
      <header className="app-header">
        <div>
          <h1>{labelByMode(languageMode, "Model Lifecycle", ZH.title)}</h1>
          <p>
            {labelByMode(
              languageMode,
              "Automatic model generation, retraining, validation, and promotion status.",
              ZH.intro
            )}
          </p>
        </div>
        <div className="header-controls">
          <button type="button" onClick={loadAll} disabled={isLoading}>
            {isLoading
              ? `${labelByMode(languageMode, "Refresh", ZH.refresh)}...`
              : labelByMode(languageMode, "Refresh", ZH.refresh)}
          </button>
          <button type="button" onClick={handleRunNow} disabled={isRunningNow}>
            {isRunningNow
              ? labelByMode(languageMode, "Running...", ZH.running)
              : labelByMode(languageMode, "Run Now", ZH.runNow)}
          </button>
        </div>
      </header>

      {error ? <p className="error-box">{error}</p> : null}
      {isLoading && !status ? (
        <p className="panel">{labelByMode(languageMode, "Loading...", ZH.loading)}</p>
      ) : null}

      <section className="panel">
        <h3>{labelByMode(languageMode, "Lifecycle Status", ZH.status)}</h3>
        <div className="detail-grid">
          <p>
            <strong>{labelByMode(languageMode, "Scheduler", ZH.scheduler)}:</strong>{" "}
            {status?.scheduler_started ? "on" : "off"}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Cadence", ZH.cadence)}:</strong>{" "}
            {status?.cadence_seconds ?? 0}s
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Last Scheduler Run", ZH.lastRun)}:</strong>{" "}
            {status?.last_run_time_utc || "N/A"}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Next Scheduler Run", ZH.nextRun)}:</strong>{" "}
            {status?.next_run_time_utc || "N/A"}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Last Retrain Time", ZH.lastRetrain)}:</strong>{" "}
            {status?.last_retrain_time_utc || "N/A"}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Next Retrain Time", ZH.nextRetrain)}:</strong>{" "}
            {status?.next_retrain_time_utc || "N/A"}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Last Workflow", ZH.lastWorkflow)}:</strong>{" "}
            {status?.last_workflow_type || "N/A"}
          </p>
        </div>
      </section>

      <section className="panel">
        <h3>{labelByMode(languageMode, "Current Production Model", ZH.production)}</h3>
        {!production ? (
          <p className="helper-text">
            {labelByMode(
              languageMode,
              "No production model is promoted yet. The fallback chain is still active.",
              "\u76ee\u524d\u5c1a\u672a\u6709\u5df2\u5347\u7d1a\u7684\u751f\u7522\u6a21\u578b\uff0c\u7cfb\u7d71\u4ecd\u6703\u4f7f\u7528\u5f8c\u5099\u5c64\u7d1a\u4fdd\u6301\u904b\u4f5c\u3002"
            )}
          </p>
        ) : (
          <div className="detail-grid">
            <p><strong>Ticker:</strong> {production.ticker}</p>
            <p><strong>Model:</strong> {production.model_name}</p>
            <p><strong>Score:</strong> {scoreText(production.validation_score)}</p>
            <p><strong>Status:</strong> {production.status}</p>
            <p><strong>Stale:</strong> {String(Boolean(production.is_stale))}</p>
            <p><strong>Updated:</strong> {production.updated_at}</p>
          </div>
        )}
      </section>

      <section className="panel">
        <h3>{labelByMode(languageMode, "Active Trigger Signals", ZH.triggers)}</h3>
        {(status?.active_triggers || []).length ? (
          <ul className="bullet-list">
            {(status?.active_triggers || []).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="helper-text">
            {labelByMode(languageMode, "No active retraining triggers right now.", ZH.noTriggers)}
          </p>
        )}
      </section>

      <section className="panel">
        <h3>{labelByMode(languageMode, "Recent Evaluation Metrics", ZH.metrics)}</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Model</th>
                <th>Status</th>
                <th>Score</th>
                <th>Accuracy</th>
                <th>F1</th>
                <th>Direction</th>
              </tr>
            </thead>
            <tbody>
              {(status?.recent_metrics || []).length ? (
                (status?.recent_metrics || []).map((item, idx) => (
                  <tr key={`${item.ticker}-${item.model_name}-${idx}`}>
                    <td>{item.ticker}</td>
                    <td>{item.model_name}</td>
                    <td>{item.status}</td>
                    <td>{scoreText(item.validation_score)}</td>
                    <td>{scoreText(item.accuracy)}</td>
                    <td>{scoreText(item.f1)}</td>
                    <td>{scoreText(item.direction_accuracy)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7}>
                    {labelByMode(
                      languageMode,
                      "No metrics available yet.",
                      "\u76ee\u524d\u6c92\u6709\u53ef\u7528\u8a55\u4f30\u6307\u6a19\u3002"
                    )}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h3>{labelByMode(languageMode, "Model Registry", ZH.registry)}</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Period</th>
                <th>Target</th>
                <th>Model</th>
                <th>Status</th>
                <th>Validated</th>
                <th>Score</th>
                <th>Stale</th>
              </tr>
            </thead>
            <tbody>
              {registry.map((item, idx) => (
                <tr key={`${item.ticker}-${item.period}-${item.target_name}-${item.model_name}-${idx}`}>
                  <td>{item.ticker}</td>
                  <td>{item.period}</td>
                  <td>{item.target_name}</td>
                  <td>{item.model_name}</td>
                  <td>{item.status}</td>
                  <td>{String(Boolean(item.is_validated))}</td>
                  <td>{scoreText(item.validation_score)}</td>
                  <td>{String(Boolean(item.is_stale))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h3>{labelByMode(languageMode, "Recent Workflow Runs", ZH.runs)}</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>{labelByMode(languageMode, "Workflow", ZH.workflow)}</th>
                <th>{labelByMode(languageMode, "Reason", ZH.reason)}</th>
                <th>{labelByMode(languageMode, "Result", ZH.result)}</th>
                <th>Tickers</th>
                <th>Success</th>
                <th>Failed</th>
                <th>Started</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.run_type}</td>
                  <td>{item.trigger_reason}</td>
                  <td>{item.status}</td>
                  <td>{item.processed_tickers}</td>
                  <td>{item.successful_models}</td>
                  <td>{item.failed_models}</td>
                  <td>{item.started_at_utc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

