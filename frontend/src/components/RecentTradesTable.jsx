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
    buy_trade: ["Buy", "買入"],
    sell_trade: ["Sell", "賣出"],
  };
  const [en, zh] = map[eventType] || [eventType || "unknown", eventType || "unknown"];
  return labelByMode(languageMode, en, zh);
}

export default function RecentTradesTable({ languageMode, trades = [] }) {
  return (
    <section className="panel">
      <h3>{labelByMode(languageMode, "Recent Trades", "近期交易")}</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{labelByMode(languageMode, "Date/Time", "日期時間")}</th>
              <th>{labelByMode(languageMode, "Type", "類型")}</th>
              <th>{labelByMode(languageMode, "Ticker", "股票代號")}</th>
              <th>{labelByMode(languageMode, "Quantity", "數量")}</th>
              <th>{labelByMode(languageMode, "Price", "價格")}</th>
              <th>{labelByMode(languageMode, "Gross Value", "成交金額")}</th>
              <th>{labelByMode(languageMode, "Balance After", "交易後現金")}</th>
              <th>{labelByMode(languageMode, "Reason", "原因")}</th>
            </tr>
          </thead>
          <tbody>
            {trades.length ? (
              trades.map((trade) => (
                <tr key={trade.id}>
                  <td>{trade.created_at}</td>
                  <td>{formatEventType(trade.event_type, languageMode)}</td>
                  <td>{trade.ticker}</td>
                  <td>{Number(trade.quantity || 0).toFixed(4)}</td>
                  <td>{formatMoney(trade.price)}</td>
                  <td>{formatMoney(trade.gross_amount)}</td>
                  <td>{formatMoney(trade.cash_balance_after)}</td>
                  <td>{trade.reason || "-"}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={8}>
                  {labelByMode(languageMode, "No executed trades yet.", "目前尚未有已執行交易。")}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
