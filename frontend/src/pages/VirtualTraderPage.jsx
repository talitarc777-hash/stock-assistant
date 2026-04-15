import React, { useEffect, useMemo, useState } from "react";

import {
  fetchLiveVirtualTraderStatus,
  fetchLiveVirtualTraderTrades,
  fetchVirtualAccountLedger,
  fetchVirtualAccountSummary,
  fetchVirtualTraderSummary,
  fetchVirtualTraderTrades,
  postVirtualAccountDeposit,
  postVirtualAccountWithdraw,
  runLiveVirtualTraderNow,
} from "../api";
import CashLedgerTable from "../components/CashLedgerTable";
import EquityChart from "../components/EquityChart";
import LineChart from "../components/LineChart";
import NewsSentimentPanel from "../components/NewsSentimentPanel";
import { fetchModelEvaluationSettings } from "../services/modelSettingsApi";

const DEFAULT_PERIOD = "5y";
const DEFAULT_MODEL = "logistic_regression";

const ZH = {
  virtualTrader: "\u865b\u64ec\u4ea4\u6613\u54e1",
  intro:
    "\u5373\u6642\u6a21\u5f0f\u6703\u4f7f\u7528\u6700\u65b0\u6a21\u578b\u8f38\u51fa\u8207\u5e02\u5834\u8cc7\u6599\uff1b\u6b77\u53f2\u6a21\u5f0f\u5247\u7528\u65bc\u56de\u653e\u8207\u6bd4\u8f03\u3002",
  ticker: "\u80a1\u7968\u4ee3\u865f",
  model: "\u6a21\u578b",
  running: "\u57f7\u884c\u4e2d...",
  runNow: "\u7acb\u5373\u57f7\u884c\u865b\u64ec\u4ea4\u6613",
  loading: "\u8f09\u5165\u4e2d...",
  liveMode: "\u5373\u6642\u865b\u64ec\u4ea4\u6613\u6a21\u5f0f",
  liveStatusTitle: "\u5373\u6642\u72c0\u614b\uff08\u8fd1\u5373\u6642\u6a21\u64ec\uff09",
  simulationOnly: "\u53ea\u5c6c\u6a21\u64ec\uff0c\u4e0d\u6703\u767c\u9001\u771f\u5be6\u4e0b\u55ae\u3002",
  delayedDataWarning:
    "\u5e02\u5834\u8207\u65b0\u805e\u8cc7\u6599\u70ba\u300c\u8fd1\u5373\u6642\u300d\u8cc7\u6599\uff0c\u53ef\u80fd\u5b58\u5728\u4f9b\u61c9\u5546\u5ef6\u9072\uff0c\u4e26\u975e\u4ea4\u6613\u6240\u7b49\u7d1a\u5be6\u6642\u4e32\u6d41\u3002",
  cash: "\u73fe\u91d1",
  holdingsValue: "\u6301\u5009\u5e02\u503c",
  totalEquity: "\u7e3d\u8cc7\u7522",
  realizedPnl: "\u5df2\u5be6\u73fe\u640d\u76ca",
  unrealizedPnl: "\u672a\u5be6\u73fe\u640d\u76ca",
  netDeposits: "\u6de8\u5165\u91d1",
  appliedContributions: "\u5df2\u5957\u7528\u6ce8\u8cc7",
  generatedAt: "\u751f\u6210\u6642\u9593",
  noLiveStatus: "\u76ee\u524d\u6c92\u6709\u5373\u6642\u72c0\u614b\u3002",
  tradingAccount: "\u4ea4\u6613\u5e33\u6236",
  totalAccountValue: "\u7e3d\u5e33\u6236\u50f9\u503c",
  amountUsd: "\u91d1\u984d\uff08USD\uff09",
  deposit: "\u65b0\u589e\u5165\u91d1",
  withdraw: "\u65b0\u589e\u63d0\u6b3e",
  currentHoldings: "\u76ee\u524d\u6301\u5009",
  quantity: "\u6578\u91cf",
  entry: "\u5165\u5834\u50f9",
  current: "\u73fe\u50f9",
  value: "\u5e02\u503c",
  noHoldings: "\u76ee\u524d\u6c92\u6709\u6301\u5009\u3002",
  latestDecisions: "\u6700\u65b0\u6c7a\u7b56",
  action: "\u52d5\u4f5c",
  price: "\u50f9\u683c",
  reason: "\u539f\u56e0",
  latestTrades: "\u6700\u65b0\u6a21\u64ec\u4ea4\u6613",
  latestReason: "\u6700\u65b0\u6c7a\u7b56\u8aaa\u660e",
  noDecision: "\u672a\u9078\u64c7\u4ea4\u6613\u8a18\u9304\u3002",
  technicalState: "\u6280\u8853\u72c0\u614b",
  newsSentiment: "\u65b0\u805e\u60c5\u7dd2",
  benchmarkStrength: "\u76f8\u5c0d\u57fa\u6e96\u5f37\u5ea6",
  confidence: "\u4fe1\u5fc3",
  historicalMode: "\u6b77\u53f2\u56de\u653e\u6a21\u5f0f",
  historicalIntro:
    "\u6b77\u53f2\u8996\u5716\u7528\u65bc\u8a55\u4f30\uff0c\u4e0a\u65b9\u7684\u5373\u6642\u6a21\u5f0f\u624d\u662f\u7576\u4e0b\u6a21\u64ec\u4ea4\u6613\u3002",
  monthlyContributionHistory: "\u6bcf\u6708\u6ce8\u8cc7\u7d00\u9304",
  totalContributions: "\u7d2f\u7a4d\u6ce8\u8cc7\u91d1\u984d",
  monthlyContribution: "\u7576\u6708\u6ce8\u8cc7\u91d1\u984d",
  noData: "\u6c92\u6709\u53ef\u7528\u8cc7\u6599",
  depositHint: "\u5165\u91d1\u6703\u4ee5\u65b0\u7684\u4e0d\u53ef\u4fee\u6539\u5206\u985e\u5e33\u4e8b\u4ef6\u8a18\u9304\u3002",
  withdrawHint: "\u63d0\u6b3e\u6703\u4ee5\u65b0\u7684\u4e0d\u53ef\u4fee\u6539\u5206\u985e\u5e33\u4e8b\u4ef6\u8a18\u9304\u3002",
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

function formatMoney(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "N/A";
  return numeric.toFixed(2);
}

export default function VirtualTraderPage({ languageMode, currentWatchlist, profileId }) {
  const [selectedTicker, setSelectedTicker] = useState(currentWatchlist[0] || "VOO");
  const [selectedModelName, setSelectedModelName] = useState(DEFAULT_MODEL);
  const [liveStatus, setLiveStatus] = useState(null);
  const [liveTrades, setLiveTrades] = useState([]);
  const [accountSummary, setAccountSummary] = useState(null);
  const [ledgerEvents, setLedgerEvents] = useState([]);
  const [cashAmount, setCashAmount] = useState("");
  const [cashReason, setCashReason] = useState("");
  const [selectedLiveTrade, setSelectedLiveTrade] = useState(null);
  const [historicalSummary, setHistoricalSummary] = useState(null);
  const [historicalTrades, setHistoricalTrades] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRunningNow, setIsRunningNow] = useState(false);
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

  async function loadAllViews(activeTicker = selectedTicker) {
    if (!profileId || !activeTicker) return;
    setIsLoading(true);
    setError("");
    try {
      const [
        statusPayload,
        tradesPayload,
        accountPayload,
        ledgerPayload,
        historicalSummaryPayload,
        historicalTradesPayload,
      ] = await Promise.all([
        fetchLiveVirtualTraderStatus(profileId, activeTicker, selectedModelName, false),
        fetchLiveVirtualTraderTrades(profileId, activeTicker, 20),
        fetchVirtualAccountSummary(profileId),
        fetchVirtualAccountLedger(profileId, 150),
        fetchVirtualTraderSummary(activeTicker, DEFAULT_PERIOD, selectedModelName, 500, profileId),
        fetchVirtualTraderTrades(activeTicker, DEFAULT_PERIOD, selectedModelName, 200, profileId),
      ]);
      setLiveStatus(statusPayload);
      setLiveTrades(tradesPayload.trades || []);
      setSelectedLiveTrade((tradesPayload.trades || [])[0] || null);
      setAccountSummary(accountPayload);
      setLedgerEvents(ledgerPayload.events || []);
      setHistoricalSummary(historicalSummaryPayload);
      setHistoricalTrades(historicalTradesPayload);
    } catch (requestError) {
      setLiveStatus(null);
      setLiveTrades([]);
      setSelectedLiveTrade(null);
      setAccountSummary(null);
      setLedgerEvents([]);
      setHistoricalSummary(null);
      setHistoricalTrades(null);
      setError(requestError.message || "Failed to load virtual trader views.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadAllViews(selectedTicker);
  }, [selectedTicker, selectedModelName, profileId]);

  async function handleRunNow() {
    if (!profileId) return;
    setIsRunningNow(true);
    setError("");
    try {
      await runLiveVirtualTraderNow(profileId, null, selectedModelName);
      await loadAllViews(selectedTicker);
    } catch (requestError) {
      setError(requestError.message || "Failed to run live virtual trader now.");
    } finally {
      setIsRunningNow(false);
    }
  }

  async function handleDeposit() {
    if (!profileId || !cashAmount) return;
    setError("");
    try {
      await postVirtualAccountDeposit(profileId, Number(cashAmount), cashReason);
      setCashAmount("");
      setCashReason("");
      await loadAllViews(selectedTicker);
    } catch (requestError) {
      setError(requestError.message || "Failed to deposit cash.");
    }
  }

  async function handleWithdraw() {
    if (!profileId || !cashAmount) return;
    setError("");
    try {
      await postVirtualAccountWithdraw(profileId, Number(cashAmount), cashReason);
      setCashAmount("");
      setCashReason("");
      await loadAllViews(selectedTicker);
    } catch (requestError) {
      setError(requestError.message || "Failed to withdraw cash.");
    }
  }

  const historicalEquityPoints = useMemo(() => {
    if (!historicalSummary?.equity_curve) return [];
    return historicalSummary.equity_curve.map((item) => ({
      date: item.date,
      total_equity: toNumeric(item.total_equity),
      cash: toNumeric(item.cash),
      holdings_value: toNumeric(item.holdings_value),
      benchmark_equity: toNumeric(item.benchmark_equity),
    }));
  }, [historicalSummary]);

  const contributionPoints = useMemo(() => {
    if (!historicalTrades?.monthly_contributions) return [];
    return historicalTrades.monthly_contributions.map((item) => ({
      date: item.date,
      cumulative_contributions: toNumeric(item.cumulative_contributions),
      amount: toNumeric(item.amount),
    }));
  }, [historicalTrades]);

  return (
    <>
      <header className="app-header">
        <div>
          <h1>{labelByMode(languageMode, "Virtual Trader", ZH.virtualTrader)}</h1>
          <p>
            {labelByMode(
              languageMode,
              "Live mode uses latest model output and current market data. Historical mode keeps replay/backtest comparison.",
              ZH.intro
            )}
          </p>
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
            {labelByMode(languageMode, "Model", ZH.model)}: {selectedModelName}
          </span>
          <button type="button" onClick={handleRunNow} disabled={isRunningNow}>
            {isRunningNow
              ? labelByMode(languageMode, "Running...", ZH.running)
              : labelByMode(languageMode, "Run Trader Now", ZH.runNow)}
          </button>
        </div>
      </header>

      {error ? <p className="error-box">{error}</p> : null}
      {isLoading ? <p className="panel">{labelByMode(languageMode, "Loading...", ZH.loading)}</p> : null}

      <section className="panel">
        <h3>{labelByMode(languageMode, "Live Trader Status (Near-live Simulation)", ZH.liveStatusTitle)}</h3>
        <p className="helper-text">
          {labelByMode(languageMode, "This is simulation only. No broker orders are sent.", ZH.simulationOnly)}
        </p>
        <p className="helper-text">
          {labelByMode(
            languageMode,
            "Market/news inputs are near-live snapshots and may be delayed by the data provider.",
            ZH.delayedDataWarning
          )}
        </p>
        {liveStatus ? (
          <div className="detail-grid">
            <p><strong>{labelByMode(languageMode, "Cash", ZH.cash)}:</strong> {formatMoney(liveStatus.account?.cash)}</p>
            <p><strong>{labelByMode(languageMode, "Holdings value", ZH.holdingsValue)}:</strong> {formatMoney(liveStatus.account?.holdings_value)}</p>
            <p><strong>{labelByMode(languageMode, "Total equity", ZH.totalEquity)}:</strong> {formatMoney(liveStatus.account?.total_equity)}</p>
            <p><strong>{labelByMode(languageMode, "Realized PnL", ZH.realizedPnl)}:</strong> {formatMoney(liveStatus.account?.realized_pnl)}</p>
            <p><strong>{labelByMode(languageMode, "Applied contributions", ZH.appliedContributions)}:</strong> {formatMoney(liveStatus.account?.total_contributions_applied)}</p>
            <p><strong>{labelByMode(languageMode, "Generated at", ZH.generatedAt)}:</strong> {liveStatus.generated_at_utc}</p>
          </div>
        ) : (
          <p>{labelByMode(languageMode, "No live status yet.", ZH.noLiveStatus)}</p>
        )}
      </section>

      <section className="panel">
        <h3>{labelByMode(languageMode, "Trading Account", ZH.tradingAccount)}</h3>
        <div className="detail-grid">
          <p><strong>{labelByMode(languageMode, "Cash", ZH.cash)}:</strong> {formatMoney(accountSummary?.cash)}</p>
          <p><strong>{labelByMode(languageMode, "Holdings value", ZH.holdingsValue)}:</strong> {formatMoney(accountSummary?.holdings_value)}</p>
          <p><strong>{labelByMode(languageMode, "Total account value", ZH.totalAccountValue)}:</strong> {formatMoney(accountSummary?.total_account_value)}</p>
          <p><strong>{labelByMode(languageMode, "Realized PnL", ZH.realizedPnl)}:</strong> {formatMoney(accountSummary?.realized_pnl)}</p>
          <p><strong>{labelByMode(languageMode, "Unrealized PnL", ZH.unrealizedPnl)}:</strong> {formatMoney(accountSummary?.unrealized_pnl)}</p>
          <p><strong>{labelByMode(languageMode, "Net deposits", ZH.netDeposits)}:</strong> {formatMoney(accountSummary?.net_deposits)}</p>
        </div>
        <div className="settings-form">
          <label>
            {labelByMode(languageMode, "Amount (USD)", ZH.amountUsd)}
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={cashAmount}
              onChange={(e) => setCashAmount(e.target.value)}
            />
          </label>
          <label>
            {labelByMode(languageMode, "Reason", ZH.reason)}
            <input type="text" value={cashReason} onChange={(e) => setCashReason(e.target.value)} />
          </label>
          <div className="settings-actions">
            <button type="button" onClick={handleDeposit}>
              {labelByMode(languageMode, "Add Deposit Event", ZH.deposit)}
            </button>
            <button type="button" onClick={handleWithdraw}>
              {labelByMode(languageMode, "Add Withdrawal Event", ZH.withdraw)}
            </button>
          </div>
          <p className="helper-text">
            {labelByMode(
              languageMode,
              "Deposits and withdrawals are saved as immutable ledger events.",
              `${ZH.depositHint} ${ZH.withdrawHint}`
            )}
          </p>
        </div>
      </section>

      <section className="panel">
        <h3>{labelByMode(languageMode, "Current holdings", ZH.currentHoldings)}</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{labelByMode(languageMode, "Ticker", ZH.ticker)}</th>
                <th>{labelByMode(languageMode, "Quantity", ZH.quantity)}</th>
                <th>{labelByMode(languageMode, "Entry", ZH.entry)}</th>
                <th>{labelByMode(languageMode, "Current", ZH.current)}</th>
                <th>{labelByMode(languageMode, "Value", ZH.value)}</th>
                <th>{labelByMode(languageMode, "Unrealized PnL", ZH.unrealizedPnl)}</th>
              </tr>
            </thead>
            <tbody>
              {(liveStatus?.holdings || []).length ? (
                (liveStatus?.holdings || []).map((item) => (
                  <tr key={`${item.ticker}-${item.entry_timestamp || "ledger"}`}>
                    <td>{item.ticker}</td>
                    <td>{Number(item.quantity).toFixed(4)}</td>
                    <td>{formatMoney(item.avg_entry_price)}</td>
                    <td>{formatMoney(item.current_price)}</td>
                    <td>{formatMoney(item.market_value)}</td>
                    <td>{formatMoney(item.unrealized_pnl)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6}>{labelByMode(languageMode, "No holdings yet.", ZH.noHoldings)}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <div className="layout-grid">
        <section className="panel">
          <h3>{labelByMode(languageMode, "Latest decisions", ZH.latestDecisions)}</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>{labelByMode(languageMode, "Action", ZH.action)}</th>
                  <th>{labelByMode(languageMode, "Price", ZH.price)}</th>
                  <th>{labelByMode(languageMode, "Reason", ZH.reason)}</th>
                </tr>
              </thead>
              <tbody>
                {(liveStatus?.latest_decisions || []).slice(0, 8).map((item) => (
                  <tr key={`${item.timestamp}-${item.ticker}-${item.action}`}>
                    <td>{item.timestamp}</td>
                    <td>{item.action}</td>
                    <td>{formatMoney(item.price)}</td>
                    <td>{item.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel">
          <h3>{labelByMode(languageMode, "Latest simulated trades", ZH.latestTrades)}</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>{labelByMode(languageMode, "Action", ZH.action)}</th>
                  <th>{labelByMode(languageMode, "Price", ZH.price)}</th>
                  <th>{labelByMode(languageMode, "Reason", ZH.reason)}</th>
                </tr>
              </thead>
              <tbody>
                {liveTrades.map((trade) => (
                  <tr
                    key={`${trade.timestamp}-${trade.ticker}-${trade.action}`}
                    className={selectedLiveTrade?.timestamp === trade.timestamp ? "selected-row" : ""}
                    onClick={() => setSelectedLiveTrade(trade)}
                  >
                    <td>{trade.timestamp}</td>
                    <td>{trade.action}</td>
                    <td>{formatMoney(trade.price)}</td>
                    <td>{trade.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <section className="panel explanation-panel">
        <h3>{labelByMode(languageMode, "Latest decision reason", ZH.latestReason)}</h3>
        {!selectedLiveTrade ? (
          <p>{labelByMode(languageMode, "No trade decision selected.", ZH.noDecision)}</p>
        ) : (
          <>
            <p><strong>{selectedLiveTrade.action_summary}</strong></p>
            <p>{selectedLiveTrade.threshold_summary}</p>
            <div className="detail-grid">
              <p><strong>{labelByMode(languageMode, "Technical state", ZH.technicalState)}:</strong> {selectedLiveTrade.technical_state_summary}</p>
              <p><strong>{labelByMode(languageMode, "News sentiment", ZH.newsSentiment)}:</strong> {selectedLiveTrade.news_sentiment_summary}</p>
              <p><strong>{labelByMode(languageMode, "Benchmark strength", ZH.benchmarkStrength)}:</strong> {selectedLiveTrade.benchmark_strength_summary}</p>
              <p><strong>{labelByMode(languageMode, "Confidence", ZH.confidence)}:</strong> {selectedLiveTrade.confidence_score !== null && selectedLiveTrade.confidence_score !== undefined ? `${(Number(selectedLiveTrade.confidence_score) * 100).toFixed(0)}%` : "N/A"}</p>
            </div>
          </>
        )}
      </section>

      <NewsSentimentPanel ticker={selectedTicker} languageMode={languageMode} />
      <CashLedgerTable languageMode={languageMode} events={ledgerEvents} />

      <section className="panel">
        <h3>{labelByMode(languageMode, "Historical Replay Mode", ZH.historicalMode)}</h3>
        <p className="helper-text">
          {labelByMode(languageMode, "Historical view is replay-style for evaluation. Live mode above is the current simulator.", ZH.historicalIntro)}
        </p>
      </section>

      {historicalSummary ? (
        <>
          <EquityChart ticker={selectedTicker} points={historicalEquityPoints} languageMode={languageMode} />
          <LineChart
            title={labelByMode(languageMode, "Monthly Contribution History", ZH.monthlyContributionHistory)}
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
                label: labelByMode(languageMode, "Monthly Contribution", ZH.monthlyContribution),
                color: "#2563eb",
                strokeWidth: 1.8,
                valueKind: "price",
              },
            ]}
            noDataMessage={labelByMode(languageMode, "No data available", ZH.noData)}
            height={180}
          />
        </>
      ) : null}
    </>
  );
}
