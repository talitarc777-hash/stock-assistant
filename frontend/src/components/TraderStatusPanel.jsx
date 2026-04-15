import React from "react";

function labelByMode(mode, en, zh) {
  if (mode === "zh") return zh;
  if (mode === "en") return en;
  return `${en} / ${zh}`;
}

function modeText(mode, languageMode) {
  if (mode === "market_open") {
    return labelByMode(languageMode, "Market Open (5 min cycle)", "開市中（每 5 分鐘）");
  }
  return labelByMode(languageMode, "Market Closed (1 hour cycle)", "休市中（每 1 小時）");
}

export default function TraderStatusPanel({
  languageMode,
  status,
  isLoading = false,
  onRefresh = null,
}) {
  const running = Boolean(status?.running);
  const recentRuns = status?.recent_runs || [];

  return (
    <section className="panel">
      <h3>{labelByMode(languageMode, "Trader Scheduler Status", "交易排程器狀態")}</h3>
      <p className="helper-text">
        {labelByMode(
          languageMode,
          "Automatic runs adapt to U.S. market hours: 5 minutes open, 1 hour closed.",
          "系統會按美股時段自動執行：開市每 5 分鐘、休市每 1 小時。"
        )}
      </p>

      {isLoading ? (
        <p>{labelByMode(languageMode, "Loading...", "載入中...")}</p>
      ) : (
        <div className="detail-grid">
          <p>
            <strong>{labelByMode(languageMode, "Status", "狀態")}:</strong>{" "}
            {running
              ? labelByMode(languageMode, "Running", "執行中")
              : labelByMode(languageMode, "Idle", "待機中")}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Mode", "模式")}:</strong>{" "}
            {modeText(status?.mode || "market_closed", languageMode)}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Last Run", "上次執行")}:</strong>{" "}
            {status?.last_run_time_utc || "N/A"}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Next Run", "下次執行")}:</strong>{" "}
            {status?.next_run_time_utc || "N/A"}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Decisions (Last Run)", "上次決策數")}:</strong>{" "}
            {status?.last_decisions_executed ?? 0} / {status?.last_decisions_total ?? 0}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Skipped Runs", "略過次數")}:</strong>{" "}
            {status?.skipped_runs_total ?? 0}
          </p>
        </div>
      )}

      {onRefresh ? (
        <div className="settings-actions">
          <button type="button" onClick={onRefresh}>
            {labelByMode(languageMode, "Refresh Status", "更新狀態")}
          </button>
        </div>
      ) : null}

      <h4>{labelByMode(languageMode, "Recent Runs", "最近執行記錄")}</h4>
      {recentRuns.length ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{labelByMode(languageMode, "Time", "時間")}</th>
                <th>{labelByMode(languageMode, "Mode", "模式")}</th>
                <th>{labelByMode(languageMode, "Executed", "已執行")}</th>
                <th>{labelByMode(languageMode, "Message", "訊息")}</th>
              </tr>
            </thead>
            <tbody>
              {recentRuns.map((item) => (
                <tr key={`${item.timestamp_utc}-${item.source}-${item.message}`}>
                  <td>{item.timestamp_utc}</td>
                  <td>{modeText(item.mode, languageMode)}</td>
                  <td>
                    {item.decisions_executed}/{item.decisions_total}
                  </td>
                  <td>{item.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p>{labelByMode(languageMode, "No run logs yet.", "暫時未有執行記錄。")}</p>
      )}
    </section>
  );
}
