import React, { useMemo } from "react";
import { getLabel } from "../constants/i18n";

function modeText(mode, languageMode) {
  if (mode === "market_open") {
    return getLabel(languageMode, "schedulerModeOpen");
  }
  return getLabel(languageMode, "schedulerModeClosed");
}

function formatRunTime(timestampUtc, languageMode) {
  if (!timestampUtc) return "N/A";
  const date = new Date(timestampUtc);
  if (Number.isNaN(date.getTime())) return timestampUtc;

  const now = new Date();
  const isSameDay =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate();
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  const isYesterday =
    date.getFullYear() === yesterday.getFullYear() &&
    date.getMonth() === yesterday.getMonth() &&
    date.getDate() === yesterday.getDate();

  const timeText = new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);

  if (isSameDay) return timeText;
  if (isYesterday) {
    return getLabel(languageMode, "yesterdayAtTime", { time: timeText });
  }
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function statusText(status, languageMode) {
  if (status === "failed") return getLabel(languageMode, "runStatusFailed");
  if (status === "partial") return getLabel(languageMode, "runStatusPartial");
  return getLabel(languageMode, "runStatusSuccess");
}

export default function RecentRunsPanel({ languageMode, status, isLoading = false, onRefresh = null }) {
  const recentRuns = useMemo(() => status?.recent_runs || [], [status?.recent_runs]);

  return (
    <section className="panel">
      <h3>{getLabel(languageMode, "recentRunsPanelTitle")}</h3>
      <p className="helper-text">{getLabel(languageMode, "recentRunsPanelIntro")}</p>
      {isLoading ? <p>{getLabel(languageMode, "loading")}</p> : null}

      {!isLoading ? (
        <div className="detail-grid">
          <p>
            <strong>{getLabel(languageMode, "schedulerStatus")}:</strong>{" "}
            {status?.running ? getLabel(languageMode, "schedulerRunning") : getLabel(languageMode, "schedulerIdle")}
          </p>
          <p>
            <strong>{getLabel(languageMode, "schedulerMode")}:</strong>{" "}
            {modeText(status?.mode || "market_closed", languageMode)}
          </p>
          <p>
            <strong>{getLabel(languageMode, "schedulerLastRun")}:</strong>{" "}
            {formatRunTime(status?.last_run_time_utc, languageMode)}
          </p>
          <p>
            <strong>{getLabel(languageMode, "schedulerNextRun")}:</strong>{" "}
            {formatRunTime(status?.next_run_time_utc, languageMode)}
          </p>
          <p>
            <strong>{getLabel(languageMode, "schedulerUsersProcessed")}:</strong>{" "}
            {status?.last_users_processed ?? 0}
          </p>
          <p>
            <strong>{getLabel(languageMode, "schedulerDecisionsExecuted")}:</strong>{" "}
            {status?.last_decisions_executed ?? 0}
          </p>
          <p>
            <strong>{getLabel(languageMode, "schedulerErrors")}:</strong> {status?.last_error_count ?? 0}
          </p>
        </div>
      ) : null}

      {onRefresh ? (
        <div className="settings-actions">
          <button type="button" onClick={onRefresh}>
            {getLabel(languageMode, "refreshStatus")}
          </button>
        </div>
      ) : null}

      <h4>{getLabel(languageMode, "recentRuns24hTitle")}</h4>
      {recentRuns.length ? (
        <div className="table-wrap recent-runs-wrap">
          <table>
            <thead>
              <tr>
                <th>{getLabel(languageMode, "recentRunsTime")}</th>
                <th>{getLabel(languageMode, "schedulerStatus")}</th>
                <th>{getLabel(languageMode, "schedulerMode")}</th>
                <th>{getLabel(languageMode, "recentRunsUsers")}</th>
                <th>{getLabel(languageMode, "recentRunsDecisions")}</th>
                <th>{getLabel(languageMode, "recentRunsErrors")}</th>
                <th>{getLabel(languageMode, "recentRunsNote")}</th>
              </tr>
            </thead>
            <tbody>
              {recentRuns.map((item) => (
                <tr key={`${item.timestamp_utc}-${item.source}-${item.message}`}>
                  <td>{formatRunTime(item.timestamp_utc, languageMode)}</td>
                  <td>
                    <span className={`run-status run-status-${item.status || "success"}`}>
                      {statusText(item.status, languageMode)}
                    </span>
                  </td>
                  <td>{modeText(item.mode, languageMode)}</td>
                  <td>{item.users_processed ?? 0}</td>
                  <td>{item.decisions_executed ?? 0}</td>
                  <td>{item.errors ?? item.error_count ?? 0}</td>
                  <td>{item.note || item.message || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p>{getLabel(languageMode, "noRunsLast24h")}</p>
      )}
    </section>
  );
}
