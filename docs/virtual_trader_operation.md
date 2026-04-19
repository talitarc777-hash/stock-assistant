# Virtual Trader Operation Guide

This document explains how the Virtual Trader works in this project:
- what data it uses
- where that data comes from
- how often it updates
- how decisions are made

## 1) Two Modes In The UI

The Virtual Trader tab combines two different workflows:

- Live virtual trader mode:
  - near-live simulation that scans a ticker universe and decides `buy` / `sell` / `hold` / `no_action` now
  - backed by endpoints in `app/api/virtual_trader.py`

- Historical replay mode:
  - replay/evaluation view based on saved model evaluation artifacts
  - backed by `/virtual-trader-summary` and `/virtual-trader-trades` in `app/api/models.py`

## 2) Live Trader: End-to-End Flow

Primary function:
- `run_live_virtual_trader_now(...)` in `app/services/live_virtual_trader.py`

Per live run:
1. Resolve scan universe:
   - uses `_resolve_user_tickers(...)`
   - default source is `get_active_universe(...)` from `app/services/universe_service.py`
   - merges user watchlist from `user_profile_service`
2. For each ticker:
   - build feature dataset with `build_feature_dataset(...)` from `app/services/research_pipeline.py`
   - fetch near-live snapshot with `get_live_market_snapshot(...)`
3. Load model candidates:
   - runtime candidates from model lifecycle service (production/validated chain)
   - fallback candidates include per-ticker model, then `GLOBAL`
4. If no model loads:
   - use built-in rule-based fallback signal
5. Apply risk and execution rules:
   - stop loss, optional take profit, confidence threshold, concentration/valuation/volatility checks
6. Persist simulated outcomes:
   - append immutable account events via account ledger
   - append decision/trade log for status and UI tables

## 3) Data Used In Live Mode

### 3.1 Price and Technical Features

Source:
- Yahoo Finance market data through `yfinance` wrappers in market-data services

Used for:
- OHLCV history (`open`, `high`, `low`, `close`, `volume`)
- technical indicators (`sma_20`, `sma_50`, `sma_200`, `rsi_14`, `macd`, volatility)
- return and benchmark-relative features

Where computed:
- `app/services/research_pipeline.py`
- `app/services/indicators.py`

### 3.2 News Sentiment Features

Source:
- Yahoo Finance news metadata via `YahooFinanceNewsProvider` in `app/services/news_service.py`

Processing:
- scoring in `app/services/news_sentiment.py`
- sentiment model preference:
  - `finbert` if dependencies/model are available
  - lexicon fallback otherwise
- outputs include:
  - same-day: `article_count`, `average_sentiment`, positive/negative ratios
  - trailing window: `*_recent_7d` features

### 3.3 Live Snapshot / Valuation

Source:
- `get_live_market_snapshot(...)` in `app/services/live_market_data_service.py`

Used for:
- current close/price used in order simulation
- valuation guardrails (for example `pe_ratio`)

## 4) Model Source And Loading

Models are loaded from local saved artifacts:
- folder pattern:
  - `data/models/<TICKER>/<period>/<target_name>/<model_name>/`
- required files:
  - `model.pkl`
  - `feature_list.json`
  - `metrics_summary.json`

Loader:
- `load_trained_model_bundle(...)` in `app/services/model_results.py`

Live loading order:
1. best runtime candidates from model lifecycle registry
2. per-ticker model
3. `GLOBAL` model
4. rule-based fallback if none load

Important:
- models are not retrained during every live run
- live run primarily performs inference + simulation

## 5) Rule-Based Fallback Strategy

If model artifacts are missing/unloadable, live mode does not stop. It falls back to `_build_rule_based_fallback(...)` in `app/services/live_virtual_trader.py`.

Fallback uses latest technical state:
- trend alignment with `close`, `sma_50`, `sma_200`
- momentum context from RSI and MACD

Fallback then still passes through standard risk/execution checks.

## 6) Update Intervals

### 6.1 Scheduler Cadence

From `app/services/market_hours_service.py`:
- market open: every 5 minutes (`300s`)
- market closed: every 1 hour (`3600s`)

The background trader scheduler starts at app startup:
- `app/main.py` lifespan starts `trader_scheduler`
- scheduler loop in `app/services/trader_scheduler.py`

### 6.2 Data Refresh Timing

During each run:
- market snapshot and feature build are executed fresh for each ticker
- news metadata is fetched during dataset construction
- news features are aggregated by day and a trailing 7-day window

So practical freshness is:
- bounded by scheduler cadence (or manual run-now calls)
- plus data-provider latency/availability

## 7) Meaning Of Status Metrics In Live UI

Displayed in live status payload:
- `universe_size`:
  - count of tickers in current scan universe
- `tickers_evaluated`:
  - how many tickers produced decisions in this run/status
- `tickers_failed`:
  - tickers skipped due to data/feature/snapshot errors
- `fallback_used_count`:
  - number of tickers that used rule-based fallback because no model could be loaded

## 8) Persistence And Logs

Storage is SQLite-based:
- profile DB path from settings (default `data/user_profiles.db`)

Live-trader related tables include:
- positions table
- trade log table
- immutable account ledger event tables (cash/trade events)

Key implementation:
- `app/services/live_virtual_trader.py`
- `app/services/account_ledger_service.py`
- `app/api/virtual_account.py`

## 9) Relevant APIs

Live trader:
- `GET /virtual-trader/live-status`
- `POST /virtual-trader/run-now`
- `GET /virtual-trader/live-trades`

Aliases:
- `/virtual-trader/status`
- `/virtual-trader/trades`
- `/virtual-trader/decisions`

Scheduler:
- `GET /virtual-trader/scheduler-status`
- `POST /virtual-trader/scheduler-run-now`
- `GET /virtual-trader/scheduler-health`

Historical replay:
- `GET /virtual-trader-summary`
- `GET /virtual-trader-trades`

