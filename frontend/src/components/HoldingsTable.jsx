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

function formatPercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "N/A";
  return `${numeric.toFixed(2)}%`;
}

export default function HoldingsTable({ languageMode, holdings = [] }) {
  return (
    <section className="panel">
      <h3>{labelByMode(languageMode, "Current Holdings", "目前持倉")}</h3>
      <p className="helper-text">
        {labelByMode(
          languageMode,
          "Only open positions are shown here. Historical buys and sells stay in the account history below.",
          "這裡只顯示目前仍持有的倉位；過往買賣紀錄會保留在下方帳戶歷史中。"
        )}
      </p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{labelByMode(languageMode, "Ticker", "股票代號")}</th>
              <th>{labelByMode(languageMode, "Quantity", "持有數量")}</th>
              <th>{labelByMode(languageMode, "Average Cost", "平均成本")}</th>
              <th>{labelByMode(languageMode, "Current Price", "現價")}</th>
              <th>{labelByMode(languageMode, "Market Value", "市值")}</th>
              <th>{labelByMode(languageMode, "Unrealized PnL", "未實現損益")}</th>
              <th>{labelByMode(languageMode, "Unrealized PnL %", "未實現損益%")}</th>
            </tr>
          </thead>
          <tbody>
            {holdings.length ? (
              holdings.map((holding) => (
                <tr key={holding.ticker}>
                  <td>{holding.ticker}</td>
                  <td>{Number(holding.quantity || 0).toFixed(4)}</td>
                  <td>{formatMoney(holding.avg_entry_price)}</td>
                  <td>{formatMoney(holding.current_price)}</td>
                  <td>{formatMoney(holding.market_value)}</td>
                  <td>{formatMoney(holding.unrealized_pnl)}</td>
                  <td>{formatPercent(holding.unrealized_pnl_pct)}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7}>
                  {labelByMode(languageMode, "No open holdings yet.", "目前尚未有持倉。")}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
