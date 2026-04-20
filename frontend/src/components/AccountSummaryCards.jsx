import React from "react";

function labelByMode(mode, en, zh) {
  if (mode === "zh") return zh;
  if (mode === "en") return en;
  return `${en} / ${zh}`;
}

function formatMoney(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "N/A";
  return numeric.toFixed(2);
}

const SUMMARY_ITEMS = [
  ["cash", "Cash", "現金"],
  ["holdings_value", "Holdings Value", "持倉市值"],
  ["total_account_value", "Total Equity", "總資產"],
  ["realized_pnl", "Realized PnL", "已實現損益"],
  ["unrealized_pnl", "Unrealized PnL", "未實現損益"],
  ["net_deposits", "Net Cash In", "淨入金"],
];

export default function AccountSummaryCards({ languageMode, summary }) {
  return (
    <section className="panel">
      <h3>{labelByMode(languageMode, "Account Summary", "帳戶摘要")}</h3>
      <p className="helper-text">
        {labelByMode(
          languageMode,
          "These values are rebuilt from immutable ledger events and current marked prices.",
          "這些數值會根據不可修改的分類帳紀錄及最新市價重新計算。"
        )}
      </p>
      <div className="detail-grid">
        {SUMMARY_ITEMS.map(([key, en, zh]) => (
          <p key={key}>
            <strong>{labelByMode(languageMode, en, zh)}:</strong> {formatMoney(summary?.[key])}
          </p>
        ))}
        <p>
          <strong>{labelByMode(languageMode, "Last Updated", "最後更新")}:</strong>{" "}
          {summary?.last_updated || summary?.as_of || "N/A"}
        </p>
        <p>
          <strong>{labelByMode(languageMode, "Latest Curve Point", "最新曲線點時間")}:</strong>{" "}
          {summary?.curve_last_point_timestamp || "N/A"}
        </p>
      </div>
    </section>
  );
}
