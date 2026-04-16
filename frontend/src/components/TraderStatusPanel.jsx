import React from "react";

function labelByMode(mode, en, zh) {
  if (mode === "zh") return zh;
  if (mode === "en") return en;
  return `${en} / ${zh}`;
}

function modeText(mode, languageMode) {
  if (mode === "market_open") {
    return labelByMode(languageMode, "Market Open (5 min cycle)", "開市時段（每 5 分鐘）");
  }
  return labelByMode(languageMode, "Market Closed (1 hour cycle)", "休市時段（每 1 小時）");
}

export default function TraderStatusPanel({ languageMode, status, isLoading = false, onRefresh = null }) {
  const recentRuns = status?.recent_runs || [];

  return (
    <section className="panel">
      <h3>{labelByMode(languageMode, "Autonomous Trader Status", "自動交易模擬狀態")}</h3>
      <p className="helper-text">
        {labelByMode(
          languageMode,
          "Trader scans the market universe automatically. No manual ticker selection is required.",
          "系統會自動掃描市場股票池，毋須手動選擇股票。"
        )}
      </p>
      {isLoading ? <p>{labelByMode(languageMode, "Loading...", "載入中...")}</p> : null}

      {!isLoading ? (
        <div className="detail-grid">
          <p>
            <strong>{labelByMode(languageMode, "Status", "狀態")}:</strong>{" "}
            {status?.running
              ? labelByMode(languageMode, "Running", "執行中")
              : labelByMode(languageMode, "Idle", "待機中")}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Mode", "模式")}:</strong>{" "}
            {modeText(status?.mode || "market_closed", languageMode)}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Last Run", "上次執行")}:</strong> {status?.last_run_time_utc || "N/A"}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Next Run", "下次執行")}:</strong> {status?.next_run_time_utc || "N/A"}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Users Processed", "處理用戶數")}:</strong>{" "}
            {status?.last_users_processed ?? 0}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Tickers Processed", "已評估股票數")}:</strong>{" "}
            {status?.last_tickers_processed ?? 0}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Tickers Failed", "失敗股票數")}:</strong>{" "}
            {status?.last_tickers_failed ?? 0}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Fallback Used", "使用後備策略")}:</strong>{" "}
            {status?.last_fallback_used ?? 0}
          </p>
          <p>
            <strong>{labelByMode(languageMode, "Trades Executed", "執行交易數")}:</strong>{" "}
            {status?.last_decisions_executed ?? 0}
          </p>
        </div>
      ) : null}

      {onRefresh ? (
        <div className="settings-actions">
          <button type="button" onClick={onRefresh}>
            {labelByMode(languageMode, "Refresh Status", "更新狀態")}
          </button>
        </div>
      ) : null}

      <h4>{labelByMode(languageMode, "Recent Runs", "最近執行紀錄")}</h4>
      {recentRuns.length ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{labelByMode(languageMode, "Time", "時間")}</th>
                <th>{labelByMode(languageMode, "Mode", "模式")}</th>
                <th>{labelByMode(languageMode, "Tickers", "股票數")}</th>
                <th>{labelByMode(languageMode, "Failed", "失敗")}</th>
                <th>{labelByMode(languageMode, "Fallback", "後備")}</th>
                <th>{labelByMode(languageMode, "Message", "訊息")}</th>
              </tr>
            </thead>
            <tbody>
              {recentRuns.map((item) => (
                <tr key={`${item.timestamp_utc}-${item.source}-${item.message}`}>
                  <td>{item.timestamp_utc}</td>
                  <td>{modeText(item.mode, languageMode)}</td>
                  <td>{item.tickers_processed}</td>
                  <td>{item.tickers_failed}</td>
                  <td>{item.fallback_used}</td>
                  <td>{item.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p>{labelByMode(languageMode, "No run logs yet.", "暫時未有執行紀錄。")}</p>
      )}
    </section>
  );
}
