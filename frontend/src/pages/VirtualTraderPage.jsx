import React, { useEffect, useMemo, useState } from "react";

import {
  fetchVirtualTraderSummary,
  fetchVirtualTraderTrades,
} from "../api";
import LineChart from "../components/LineChart";
import EquityChart from "../components/EquityChart";
import { fetchModelEvaluationSettings } from "../services/modelSettingsApi";

const DEFAULT_PERIOD = "5y";
const DEFAULT_MODEL = "logistic_regression";

const ZH = {
  title: "虛擬交易員",
  intro: "查看模型驅動的模擬資金、交易紀錄與與 VOO 的比較。",
  ticker: "股票代號",
  currentCash: "現金",
  holdings: "持倉",
  finalEquity: "最終資產",
  realizedPnl: "已實現盈虧",
  unrealizedPnl: "未實現盈虧",
  tradeLog: "交易紀錄",
  equityCurve: "資產曲線",
  contributionHistory: "每月注資紀錄",
  benchmarkComparison: "與 VOO 比較",
  action: "動作",
  reason: "原因",
  explanation: "交易解釋",
  loading: "載入中...",
  noData: "未有已儲存的虛擬交易結果。請先執行 virtual-trader。",
  benchmarkEquity: "VOO 資產",
  strategyEquity: "策略資產",
  amount: "金額",
  totalContributions: "累積注資",
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

export default function VirtualTraderPage({ languageMode, currentWatchlist, profileId }) {
  const [selectedTicker, setSelectedTicker] = useState(currentWatchlist[0] || "VOO");
  const [selectedModelName, setSelectedModelName] = useState(DEFAULT_MODEL);
  const [summaryData, setSummaryData] = useState(null);
  const [tradesData, setTradesData] = useState(null);
  const [selectedTrade, setSelectedTrade] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!currentWatchlist.length) return;
    if (!currentWatchlist.includes(selectedTicker)) {
      setSelectedTicker(currentWatchlist[0]);
    }
  }, [currentWatchlist.join(","), selectedTicker]);

  useEffect(() => {
    let isActive = true;
    async function loadModelSettings() {
      try {
        const settings = await fetchModelEvaluationSettings(profileId);
        if (!isActive) return;
        setSelectedModelName(settings.selected_model_name || DEFAULT_MODEL);
      } catch {
        if (!isActive) return;
        setSelectedModelName(DEFAULT_MODEL);
      }
    }
    if (profileId) {
      loadModelSettings();
    }
    return () => {
      isActive = false;
    };
  }, [profileId]);

  useEffect(() => {
    if (!selectedTicker) return;

    let isActive = true;
    async function loadVirtualTrader() {
      setIsLoading(true);
      setError("");
      try {
        const [summary, trades] = await Promise.all([
          fetchVirtualTraderSummary(selectedTicker, DEFAULT_PERIOD, selectedModelName, 500, profileId),
          fetchVirtualTraderTrades(selectedTicker, DEFAULT_PERIOD, selectedModelName, 200, profileId),
        ]);
        if (!isActive) return;
        setSummaryData(summary);
        setTradesData(trades);
        setSelectedTrade((trades.trade_log && trades.trade_log.length ? trades.trade_log[trades.trade_log.length - 1] : null));
      } catch (requestError) {
        if (!isActive) return;
        setSummaryData(null);
        setTradesData(null);
        setSelectedTrade(null);
        setError(requestError.message || "Failed to load virtual trader results.");
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    loadVirtualTrader();
    return () => {
      isActive = false;
    };
  }, [selectedTicker, selectedModelName, profileId]);

  const equityPoints = useMemo(() => {
    if (!summaryData?.equity_curve) return [];
    return summaryData.equity_curve.map((item) => ({
      date: item.date,
      total_equity: toNumeric(item.total_equity),
      cash: toNumeric(item.cash),
      holdings_value: toNumeric(item.holdings_value),
      benchmark_equity: toNumeric(item.benchmark_equity),
    }));
  }, [summaryData]);

  const contributionPoints = useMemo(() => {
    if (!tradesData?.monthly_contributions) return [];
    return tradesData.monthly_contributions.map((item) => ({
      date: item.date,
      cumulative_contributions: toNumeric(item.cumulative_contributions),
      amount: toNumeric(item.amount),
    }));
  }, [tradesData]);

  const summary = summaryData?.summary;
  const benchmark = summaryData?.benchmark_comparison;

  return (
    <>
      <header className="app-header">
        <div>
          <h1>{labelByMode(languageMode, "Virtual Trader", ZH.title)}</h1>
          <p>{labelByMode(languageMode, "Review model-driven simulated cash, trades, and comparison versus VOO.", ZH.intro)}</p>
        </div>
        <div className="header-controls">
          <label htmlFor="virtual-ticker-select">{labelByMode(languageMode, "Ticker", ZH.ticker)}</label>
          <select
            id="virtual-ticker-select"
            value={selectedTicker}
            onChange={(event) => setSelectedTicker(event.target.value)}
          >
            {(currentWatchlist.length ? currentWatchlist : ["VOO"]).map((ticker) => (
              <option key={ticker} value={ticker}>
                {ticker}
              </option>
            ))}
          </select>
          <span className="helper-chip">
            {labelByMode(languageMode, "Model", "模型")}: {selectedModelName}
          </span>
        </div>
      </header>

      {error ? <p className="error-box">{error}</p> : null}
      {isLoading ? <p className="panel">{labelByMode(languageMode, "Loading...", ZH.loading)}</p> : null}
      {!isLoading && !summary && !error ? (
        <p className="panel">{labelByMode(languageMode, "No saved virtual trader results yet. Run the virtual-trader command first.", ZH.noData)}</p>
      ) : null}

      {summary ? (
        <>
          <div className="layout-grid">
            <section className="panel">
              <h3>{labelByMode(languageMode, "Account Snapshot", "帳戶概覽")}</h3>
              <div className="detail-grid">
                <p><strong>{labelByMode(languageMode, "Current cash", ZH.currentCash)}:</strong> {summary.cash.toFixed(2)}</p>
                <p><strong>{labelByMode(languageMode, "Holdings", ZH.holdings)}:</strong> {summary.holdings.toFixed(4)}</p>
                <p><strong>{labelByMode(languageMode, "Final equity", ZH.finalEquity)}:</strong> {summary.final_equity.toFixed(2)}</p>
                <p><strong>{labelByMode(languageMode, "Realized PnL", ZH.realizedPnl)}:</strong> {summary.realized_pnl.toFixed(2)}</p>
                <p><strong>{labelByMode(languageMode, "Unrealized PnL", ZH.unrealizedPnl)}:</strong> {summary.unrealized_pnl.toFixed(2)}</p>
                <p><strong>{labelByMode(languageMode, "Total contributions", ZH.totalContributions)}:</strong> {summary.total_contributions.toFixed(2)}</p>
              </div>
            </section>

            <section className="panel">
              <h3>{labelByMode(languageMode, "Comparison vs VOO", ZH.benchmarkComparison)}</h3>
              <div className="detail-grid">
                <p><strong>{labelByMode(languageMode, "Strategy equity", ZH.strategyEquity)}:</strong> {summary.final_equity.toFixed(2)}</p>
                <p><strong>{labelByMode(languageMode, "VOO equity", ZH.benchmarkEquity)}:</strong> {benchmark?.final_equity?.toFixed(2)}</p>
                <p><strong>{labelByMode(languageMode, "Strategy return", "策略回報")}:</strong> {summary.return_on_contributions_pct.toFixed(2)}%</p>
                <p><strong>{labelByMode(languageMode, "VOO return", "VOO 回報")}:</strong> {benchmark?.return_on_contributions_pct?.toFixed(2)}%</p>
                <p><strong>{labelByMode(languageMode, "Outperformance", "相對表現")}:</strong> {summary.outperformance_vs_benchmark_pct_points.toFixed(2)} pct</p>
              </div>
            </section>
          </div>

          <EquityChart
            ticker={selectedTicker}
            points={equityPoints}
            languageMode={languageMode}
          />

          <LineChart
            title={labelByMode(languageMode, "Monthly Contribution History", ZH.contributionHistory)}
            subtitle={`Ticker: ${selectedTicker} | Last 6 Months`}
            points={contributionPoints}
            xAxisLabel="Date"
            yAxisLabel="Price (USD)"
            yValueKind="price"
            lines={[
              {
                key: "cumulative_contributions",
                label: labelByMode(languageMode, "Total Contributions", ZH.totalContributions),
                color: "#047857",
                strokeWidth: 2.4,
                valueKind: "price",
              },
              {
                key: "amount",
                label: labelByMode(languageMode, "Monthly Contribution", "每月投入"),
                color: "#2563eb",
                strokeWidth: 1.8,
                valueKind: "price",
              },
            ]}
            noDataMessage={labelByMode(languageMode, "No data available", "沒有可用資料")}
            height={180}
          />

          <div className="layout-grid">
            <section className="panel">
              <h3>{labelByMode(languageMode, "Trade Log", ZH.tradeLog)}</h3>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>{labelByMode(languageMode, "Action", ZH.action)}</th>
                      <th>Price</th>
                      <th>Qty</th>
                      <th>{labelByMode(languageMode, "Reason", ZH.reason)}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(tradesData?.trade_log || []).slice().reverse().map((trade) => (
                      <tr
                        key={`${trade.timestamp}-${trade.action}-${trade.price}`}
                        className={selectedTrade?.timestamp === trade.timestamp && selectedTrade?.action === trade.action ? "selected-row" : ""}
                        onClick={() => setSelectedTrade(trade)}
                      >
                        <td>{trade.timestamp}</td>
                        <td>{trade.action}</td>
                        <td>{Number(trade.price).toFixed(2)}</td>
                        <td>{Number(trade.quantity).toFixed(4)}</td>
                        <td>{trade.trade_reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="panel explanation-panel">
              <h3>{labelByMode(languageMode, "Trade Explanation", ZH.explanation)}</h3>
              {!selectedTrade ? (
                <p>{labelByMode(languageMode, "Select a trade to inspect the reason and thresholds.", "選擇一筆交易以查看原因與觸發門檻。")}</p>
              ) : (
                <>
                  <p><strong>{selectedTrade.action_summary}</strong></p>
                  <p>{selectedTrade.explanation}</p>
                  <p className="helper-text">{selectedTrade.threshold_summary}</p>
                  <div className="detail-grid">
                    <p><strong>{labelByMode(languageMode, "Technical State", "技術狀態")}:</strong> {selectedTrade.technical_state_summary}</p>
                    <p><strong>{labelByMode(languageMode, "News Sentiment", "新聞情緒")}:</strong> {selectedTrade.news_sentiment_summary}</p>
                    <p><strong>{labelByMode(languageMode, "Benchmark Strength", "相對基準強度")}:</strong> {selectedTrade.benchmark_strength_summary}</p>
                    <p><strong>{labelByMode(languageMode, "Confidence", "信心")}:</strong> {selectedTrade.model_confidence !== null && selectedTrade.model_confidence !== undefined ? `${(Number(selectedTrade.model_confidence) * 100).toFixed(0)}%` : "N/A"}</p>
                  </div>
                </>
              )}
            </section>
          </div>

          <section className="panel">
            <h3>{labelByMode(languageMode, "Monthly Contribution History", ZH.contributionHistory)}</h3>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>{labelByMode(languageMode, "Amount", ZH.amount)}</th>
                    <th>{labelByMode(languageMode, "Total Contributions", ZH.totalContributions)}</th>
                  </tr>
                </thead>
                <tbody>
                  {(tradesData?.monthly_contributions || []).slice().reverse().map((item) => (
                    <tr key={`${item.date}-${item.cumulative_contributions}`}>
                      <td>{item.date}</td>
                      <td>{Number(item.amount).toFixed(2)}</td>
                      <td>{Number(item.cumulative_contributions).toFixed(2)}</td>
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
