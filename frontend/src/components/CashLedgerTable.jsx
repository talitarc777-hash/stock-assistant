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

function formatEventType(eventType, languageMode) {
  const map = {
    monthly_contribution: ["Monthly Contribution", "\u6bcf\u6708\u6ce8\u8cc7"],
    manual_deposit: ["Manual Deposit", "\u624b\u52d5\u5165\u91d1"],
    withdrawal: ["Withdrawal", "\u63d0\u6b3e"],
    buy_trade: ["Buy Trade", "\u8cb7\u5165\u4ea4\u6613"],
    sell_trade: ["Sell Trade", "\u8ce3\u51fa\u4ea4\u6613"],
    fee: ["Fee", "\u8cbb\u7528"],
  };
  const [en, zh] = map[eventType] || [eventType || "unknown", eventType || "unknown"];
  return labelByMode(languageMode, en, zh);
}

export default function CashLedgerTable({ languageMode, events }) {
  return (
    <section className="panel">
      <h3>
        {labelByMode(
          languageMode,
          "Account Ledger (Immutable Records)",
          "\u5e33\u6236\u5206\u985e\u5e33\uff08\u4e0d\u53ef\u4fee\u6539\u8a18\u9304\uff09"
        )}
      </h3>
      <p className="helper-text">
        {labelByMode(
          languageMode,
          "All cash movements and simulated trades are permanently recorded.",
          "\u6240\u6709\u73fe\u91d1\u8b8a\u52d5\u8207\u6a21\u64ec\u4ea4\u6613\u5747\u6703\u6c38\u4e45\u8a18\u9304\u3002"
        )}
      </p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{labelByMode(languageMode, "Timestamp", "\u6642\u9593")}</th>
              <th>{labelByMode(languageMode, "Event Type", "\u4e8b\u4ef6\u985e\u578b")}</th>
              <th>{labelByMode(languageMode, "Amount (USD)", "\u91d1\u984d\uff08USD\uff09")}</th>
              <th>{labelByMode(languageMode, "Ticker", "\u80a1\u7968\u4ee3\u865f")}</th>
              <th>{labelByMode(languageMode, "Reason / Note", "\u539f\u56e0 / \u5099\u8a3b")}</th>
              <th>{labelByMode(languageMode, "Source", "\u4f86\u6e90")}</th>
            </tr>
          </thead>
          <tbody>
            {(events || []).length ? (
              events.map((event) => (
                <tr key={`${event.id}`}>
                  <td>{event.created_at}</td>
                  <td>{formatEventType(event.event_type, languageMode)}</td>
                  <td>{formatMoney(event.amount)}</td>
                  <td>{event.ticker || "-"}</td>
                  <td>{event.reason || "-"}</td>
                  <td>{event.source || "-"}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6}>
                  {labelByMode(
                    languageMode,
                    "No ledger records yet.",
                    "\u76ee\u524d\u5c1a\u7121\u5206\u985e\u5e33\u8a18\u9304\u3002"
                  )}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
