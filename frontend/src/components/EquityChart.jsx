import React from "react";

import Chart from "./Chart";

export default function EquityChart({ ticker, points = [], languageMode = "both" }) {
  const title =
    languageMode === "zh"
      ? "虛擬交易資產曲線"
      : languageMode === "en"
        ? "Virtual Trader Equity Curve"
        : "Virtual Trader Equity Curve / 虛擬交易資產曲線";
  const subtitle =
    languageMode === "zh"
      ? `股票: ${ticker}`
      : languageMode === "en"
        ? `Ticker: ${ticker}`
        : `Ticker: ${ticker} / 股票: ${ticker}`;

  return (
    <Chart
      title={title}
      subtitle={subtitle}
      points={points}
      xAxisLabel="Date"
      yAxisLabel="Portfolio Value (USD)"
      yValueKind="price"
      lines={[
        {
          key: "total_equity",
          label: "Portfolio Value",
          color: "#334155",
          strokeWidth: 2.8,
          valueKind: "price",
        },
        {
          key: "cash",
          label: "Cash",
          color: "#0891b2",
          strokeWidth: 1.9,
          valueKind: "price",
        },
        {
          key: "holdings_value",
          label: "Invested Value",
          color: "#7c3aed",
          strokeWidth: 1.9,
          valueKind: "price",
        },
        {
          key: "benchmark_equity",
          label: "VOO Buy-and-Hold",
          color: "#16a34a",
          strokeWidth: 2.2,
          valueKind: "price",
          dashArray: "5 4",
        },
      ]}
      noDataMessage="No data available"
      showRangeSelector
      defaultRange="6M"
    />
  );
}
