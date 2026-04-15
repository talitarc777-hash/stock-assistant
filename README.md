# stock-assistant

Beginner-friendly Python project for a **stock analysis assistant**.

This project is a **decision-support tool**, not an auto-trader.  
It is designed to analyze ETFs/stocks (such as `VOO`, `SPY`, `QQQ`, `AAPL`, `MSFT`, `NVDA`) and later provide simple **buy / hold / reduce-risk** style suggestions based on trend + momentum rules.

## Project Structure

```text
stock-assistant/
+-- app/
|   +-- api/
|   +-- core/
|   +-- services/
|   +-- models/
|   +-- backtest/
|   +-- main.py
+-- tests/
+-- scripts/
+-- .env.example
+-- requirements.txt
+-- frontend/
+   +-- src/
+   +-- package.json
+-- README.md
```

## Prerequisites (Windows + VS Code)

1. Install Python 3.10+ from: https://www.python.org/downloads/windows/
2. Install VS Code: https://code.visualstudio.com/
3. Install VS Code Python extension (`ms-python.python`).
4. Install Node.js 18+ from: https://nodejs.org/

## Setup Steps (VS Code Terminal)

Open this folder in VS Code, then run:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

When the server starts, open:

- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Run Backend + Frontend Together

Use two terminals in VS Code.

Terminal 1 (backend):

```powershell
.\.venv312\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Terminal 2 (frontend):

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Open the dashboard at:

- http://127.0.0.1:5173

The dashboard now also includes a shared settings page at:

- http://127.0.0.1:5173/settings

The dashboard home page also shows a shared current-alerts panel that reads from:

- `GET /user-alerts/scan?user_id=...`

To run backend, dashboard, and Discord bot together, use three terminals:

Terminal 1:

```powershell
.\.venv312\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Terminal 2:

```powershell
cd frontend
npm run dev
```

Terminal 3:

```powershell
.\.venv312\Scripts\Activate.ps1
python bot/main.py
```

## Discord Bot

The project includes a simple Python Discord bot in `bot/`.

Bot environment settings in `.env`:

- `DISCORD_BOT_TOKEN`
- `BACKEND_BASE_URL`
- `COMMAND_PREFIX`
- `ALLOWED_CHANNEL_IDS`
- `WATCHLIST_TICKERS`
- `REPLY_LANGUAGE`
- `USER_SETTINGS_PATH`

Run the bot:

```powershell
python bot/main.py
```

Per-user settings:

- Shared settings are primarily stored in backend SQLite at `PROFILE_DB_PATH`
- The bot still keeps local JSON fallback storage at `USER_SETTINGS_PATH` for safe offline behavior
- Settings are saved per user ID
- If a user has no saved settings yet, the backend creates a default profile on first access
- Per-user language overrides the global `REPLY_LANGUAGE` default

Shared profile model:

- The backend is now the main source of truth for user profiles in SQLite at `PROFILE_DB_PATH`
- Shared fields include language, compact mode, default watchlist, alert settings, and alert watchlist
- Discord reads shared settings from the backend first, then falls back to local bot storage if the profile API is unavailable
- The dashboard reads and writes the same shared backend profile

Available Discord commands:

- `!help`
- `!settings`
- `!setlang en`
- `!setlang zh`
- `!setlang bilingual`
- `!setcompact on`
- `!setcompact off`
- `!setwatchlist VOO,QQQ,AAPL`
- `!resetsettings`
- `!analyze VOO`
- `!forecast NVDA`
- `!watchlist`
- `!alerts`

Natural-language examples:

- `set my language to Chinese`
- `change language to English`
- `use bilingual mode`
- `show my settings`
- `turn on compact mode`
- `disable compact mode`
- `add Tesla to my watchlist`
- `add AAPL and NVDA to my watchlist`
- `remove TSLA from my watchlist`
- `show my watchlist`
- `analyze VOO`
- `check Apple`
- `what do you think about NVDA`
- `forecast QQQ`
- `what is the outlook for Tesla`

Supported language-setting phrases:

- `set my language to Chinese`
- `change language to English`
- `reply in Chinese`
- `use bilingual mode`
- `speak in English and Chinese`

Watchlist add/remove examples:

- `add Tesla to my watchlist`
- `add TSLA`
- `add AAPL and NVDA to my watchlist`
- `remove Tesla from my watchlist`
- `remove TSLA`
- `delete AAPL from my watchlist`

Natural-language limitations:

- Parsing is rule-based, not AI-based
- Explicit `!commands` still work first and are the most reliable
- The bot only responds to clear supported phrases
- If a company name is ambiguous, the bot will ask you to use the ticker symbol

How settings affect replies:

- `language`
  controls which action summary and explanation bullets are used
- `compact_mode`
  shortens `!analyze`, `!forecast`, and `!watchlist` output
- `default_watchlist`
  is used automatically by `!watchlist`; if empty, the bot falls back to the system default watchlist

Resetting settings:

- Use `!resetsettings` to clear your saved preferences and return to defaults

Watchlist sync:

- Discord `!watchlist`, `!addticker`, `!removeticker`, and `!setwatchlist` now use the shared backend profile watchlist
- The dashboard settings page and watchlist manager update the same watchlist
- If a user has no saved watchlist, the backend falls back to `WATCHLIST_TICKERS`

Alert sync:

- Alert preferences are stored with the shared user profile
- Shared alert fields include `alert_enabled`, `alert_threshold_high`, `alert_threshold_low`, and `alert_watchlist`
- Discord `!alerts` now tries the shared backend alert scan first, then falls back to local alert logic if needed
- Duplicate alert spam is reduced by storing the last triggered state per user/ticker/rule in SQLite

Current local-user limitation:

- There is no full authentication layer yet
- Discord uses the real Discord user ID as `user_id`
- The dashboard uses a profile ID you can edit in the Settings page
- To make dashboard and Discord share the exact same profile, use the same profile ID in both places

## Daily Scan + OpenClaw Placeholder

Watchlist config file:

- `config/watchlist.json`

Run a local scan:

```powershell
python scripts/daily_scan.py
```

Run scan and invoke OpenClaw adapter placeholder (log-only):

```powershell
python scripts/daily_scan.py --send-openclaw
```

Current behavior:

- Generates ranked watchlist summary
- Prints alert lines in an OpenClaw-friendly message format
- Does **not** place trades or connect to any broker
- Uses a modular adapter in `app/services/openclaw_adapter.py` for future webhook/channel integration

## Paper Trading Simulation (Simulation Only)

This module is for **simulation only**:

- No real-money trading
- No broker execution
- No automated order placement
- Only hypothetical ?œwould buy / would sell??events

API endpoint:

- `GET /paper-status?ticker=VOO`

Script:

```powershell
python scripts/paper_run.py --ticker VOO --period 5y --initial-cash 10000
```

## Automation CLI

CLI entry script:

- `scripts/cli.py`

Exact commands:

```powershell
python scripts/cli.py analyze-ticker --ticker VOO
python scripts/cli.py analyze-watchlist
python scripts/cli.py backtest --ticker VOO --period 10y
python scripts/cli.py export-report --ticker VOO
```

Notes:

- `analyze-watchlist` reads `config/watchlist.json`
- `export-report` saves JSON files to the `reports/` folder

Extra useful variants:

```powershell
python scripts/cli.py analyze-ticker --ticker MSFT --period 5y --benchmark VOO
python scripts/cli.py analyze-watchlist --config config/watchlist.json --period 5y
python scripts/cli.py backtest --ticker QQQ --period 10y --transaction-cost-pct 0.001
python scripts/cli.py export-report --ticker NVDA --period 5y --transaction-cost-pct 0.001
```

## VS Code Tasks And Launch

Added files:

- `.vscode/tasks.json`
- `.vscode/launch.json`

Included run targets:

- Run API (FastAPI/Uvicorn)
- Run daily watchlist scan
- Run backtest (VOO 10y)

## Market Data API

Endpoint:

- `GET /price-history?ticker=VOO&period=5y`
- `GET /indicators?ticker=VOO&period=5y`
- `GET /analyze?ticker=VOO&period=5y`
- `GET /compare-to-benchmark?ticker=QQQ&benchmark=VOO&period=5y`
- `GET /watchlist-analyze?tickers=VOO,SPY,QQQ,AAPL,MSFT,NVDA`
- `GET /backtest?ticker=VOO&period=10y`
- `GET /chart-data?ticker=VOO&period=5y`
- `GET /summary-dashboard?tickers=VOO,SPY,QQQ,AAPL,MSFT,NVDA`
- `GET /paper-status?ticker=VOO`
- `GET /forecast?ticker=VOO&period=2y`
- `GET /forecast-history?ticker=VOO`
- `GET /user-profile?user_id=...`
- `POST /user-profile/settings`
- `GET /user-watchlist?user_id=...`
- `POST /user-watchlist/add`
- `POST /user-watchlist/remove`
- `GET /user-alert-settings?user_id=...`
- `POST /user-alert-settings/update`
- `GET /user-alerts/scan?user_id=...`
- `GET /user-alerts/enabled-users`
- `POST /user-profile/reset`

Example (PowerShell):

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/price-history?ticker=VOO&period=5y"
Invoke-RestMethod "http://127.0.0.1:8000/indicators?ticker=VOO&period=5y"
Invoke-RestMethod "http://127.0.0.1:8000/analyze?ticker=VOO&period=5y"
Invoke-RestMethod "http://127.0.0.1:8000/compare-to-benchmark?ticker=QQQ&benchmark=VOO&period=5y"
Invoke-RestMethod "http://127.0.0.1:8000/watchlist-analyze?tickers=VOO,SPY,QQQ,AAPL,MSFT,NVDA"
Invoke-RestMethod "http://127.0.0.1:8000/backtest?ticker=VOO&period=10y"
Invoke-RestMethod "http://127.0.0.1:8000/backtest?ticker=VOO&period=10y&transaction_cost_pct=0.001"
Invoke-RestMethod "http://127.0.0.1:8000/chart-data?ticker=VOO&period=5y"
Invoke-RestMethod "http://127.0.0.1:8000/summary-dashboard?tickers=VOO,SPY,QQQ,AAPL,MSFT,NVDA"
Invoke-RestMethod "http://127.0.0.1:8000/paper-status?ticker=VOO"
Invoke-RestMethod "http://127.0.0.1:8000/forecast?ticker=VOO&period=2y"
Invoke-RestMethod "http://127.0.0.1:8000/forecast-history?ticker=VOO"
Invoke-RestMethod "http://127.0.0.1:8000/user-profile?user_id=demo-user"
```

Unified profile endpoints:

- `GET /user-profile?user_id=demo-user`
  returns the shared profile row and creates it on first access if needed
- `POST /user-profile/settings`
  updates shared language, compact mode, and default watchlist
- `GET /user-watchlist?user_id=demo-user`
  returns the user watchlist or the system default fallback
- `POST /user-watchlist/add`
  adds one ticker to the shared watchlist
- `POST /user-watchlist/remove`
  removes one ticker from the shared watchlist
- `GET /user-alert-settings?user_id=demo-user`
  returns shared alert preferences
- `POST /user-alert-settings/update`
  updates alert enabled state, thresholds, alert watchlist, and delivery source
- `GET /user-alerts/scan?user_id=demo-user`
  returns user-specific deduplicated alert events for Discord-friendly delivery
- `GET /user-alerts/enabled-users`
  returns all alert-enabled users for scheduler or batch delivery integration
- `POST /user-profile/reset`
  resets a shared user profile back to default language, compact mode, watchlist, and alert preferences

Response includes:

- `summary`: ticker, period, row count, date range, latest close
- `latest_10_rows`: last 10 OHLCV rows with columns:
  `date`, `open`, `high`, `low`, `close`, `adj_close`, `volume`
- `/indicators` includes:
  `latest_close`, `latest_snapshot` (latest indicator values), and `latest_30_rows`
- `/analyze` includes:
  `ticker`, `latest_close`, `score_breakdown`, `label`, `action_summary`, `explanation_bullets`
- `/compare-to-benchmark` includes:
  1m/3m/6m/12m returns, benchmark returns, excess returns, and `benchmark_strength_score`
- `/watchlist-analyze` returns:
  all requested tickers ranked by score (descending), plus any per-ticker failures
- `/backtest` includes:
  `metrics_summary`, `trade_log_preview`, and `equity_curve`
- `/chart-data` includes:
  daily OHLCV + SMA/RSI/MACD series, plus a score-over-time series (ISO dates, downsampled for payload size)
- `/summary-dashboard` includes compact per-ticker fields:
  latest close, daily % change, score, label, action summary, above SMA200, RSI, and MACD bullish flag
- `/paper-status` includes simulation-only cash/position/PnL state and hypothetical event history
- `/forecast` includes scenario-based 5d/20d outlook, trend regime, expected range,
  support/resistance, confidence score, bilingual summaries, and explanation bullets
- `/forecast-history` returns stored forecast snapshots (timestamp, outlook, expected range, confidence)
  for later forecast-vs-actual evaluation

## Service Usage (Python)

You can call the market data service directly:

```python
from app.services.market_data import get_price_history, get_price_history_for_tickers
from app.services.indicators import add_technical_indicators

df = get_price_history("AAPL", period="5y")
df_with_indicators = add_technical_indicators(df)
batch = get_price_history_for_tickers(["VOO", "SPY", "QQQ"], period="1y")
```

`get_price_history_for_tickers(...)` is a small helper for multi-ticker fetches and skips invalid/empty symbols gracefully.

Indicator columns added by `add_technical_indicators(...)`:

- `sma_20`, `sma_50`, `sma_200`
- `ema_12`, `ema_26`
- `rsi_14`
- `macd_line`, `macd_signal`, `macd_histogram`
- `avg_volume_20`
- `distance_from_52w_high_pct`
- `rolling_volatility_20_pct`
- `drawdown_from_peak_pct`

## Research Dataset Pipeline

You can build a model-ready daily feature dataset with:

```python
from app.services.research_pipeline import build_and_save_feature_dataset

artifact = build_and_save_feature_dataset(
    ticker="AAPL",
    period="5y",
    benchmark="VOO",
)

print(artifact.dataset_path)
print(artifact.metadata_path)
```

Saved folder structure:

- `data/research/<TICKER>/<PERIOD>/features.csv`
- `data/research/<TICKER>/<PERIOD>/metadata.json`

Main dataset column groups:

- Raw price data:
  `date`, `ticker`, `benchmark`, `open`, `high`, `low`, `close`, `adj_close`, `volume`
- Return features:
  `return_1d_pct`, `return_5d_pct`, `return_20d_pct`, `return_1m_pct`, `return_3m_pct`, `return_6m_pct`, `return_12m_pct`
- Technical indicators:
  `sma_20`, `sma_50`, `sma_200`, `ema_12`, `ema_26`, `rsi_14`, `macd_line`, `macd_signal`, `macd_histogram`,
  `avg_volume_20`, `rolling_volatility_20_pct`, `distance_from_52w_high_pct`, `drawdown_from_peak_pct`
- Benchmark-relative features versus `VOO`:
  `benchmark_return_*_pct`, `excess_return_*_pct`, `benchmark_strength_score`
- News sentiment features:
  `news_article_count`, `news_sentiment_score`, `news_sentiment_3d_avg`, `news_sentiment_7d_avg`
- Prediction targets:
  `target_5d_return`, `target_5d_updown`, `target_20d_regime`

Target notes:

- `target_5d_return` is the forward 5-trading-day return in percent
- `target_5d_updown` is `1` if the forward 5-day return is positive, else `0`
- `target_20d_regime` uses a simple rule:
  `bullish` if future 20-day return >= 2%, `bearish` if <= -2%, otherwise `neutral`

News-sentiment note:

- The built-in sentiment layer uses recent Yahoo Finance news headlines and summaries through `yfinance`
- News coverage can be sparse, so older rows may have zero sentiment values
- This is meant as a lightweight research feature, not a production-grade sentiment feed

## What Exists Right Now

- FastAPI backend scaffold
- `GET /health` endpoint
- `GET /price-history?ticker=VOO&period=5y` endpoint
- `GET /indicators?ticker=VOO&period=5y` endpoint
- `GET /analyze?ticker=VOO&period=5y` endpoint
- `GET /compare-to-benchmark?ticker=QQQ&benchmark=VOO&period=5y` endpoint
- `GET /watchlist-analyze?tickers=VOO,SPY,QQQ,AAPL,MSFT,NVDA` endpoint
- `GET /backtest?ticker=VOO&period=10y` endpoint
- `GET /chart-data?ticker=VOO&period=5y` endpoint
- `GET /summary-dashboard?tickers=VOO,SPY,QQQ,AAPL,MSFT,NVDA` endpoint
- `GET /paper-status?ticker=VOO` endpoint
- `GET /forecast?ticker=VOO&period=2y` endpoint
- `GET /forecast-history?ticker=VOO` endpoint
- Typed settings loaded from `.env`
- Market data service using `yfinance`
- Technical indicator service with validation
- Explainable scoring engine (trend, momentum, confirmation, risk penalties)
- Benchmark-relative strength analysis vs VOO (or custom benchmark)
- Beginner-friendly long-only backtest engine with optional transaction cost
- Chart-ready and dashboard summary endpoints for frontend integration
- Minimal React + Vite dashboard (`frontend/`) connected to FastAPI
- Paper-trading simulator module (simulation only, no broker integration)
- Scenario-based forecast module (not a guaranteed prediction)
- Local SQLite forecast snapshot persistence for future evaluation

## Next Suggested Steps

1. Add a market data service (using `yfinance`) in `app/services/`.
2. Add simple trend/momentum rules and suggestion labels in `app/models/` + `app/services/`.
3. Expose an analysis endpoint in `app/api/`.
4. Add basic backtests in `app/backtest/`.
5. Later integrate dashboard UI and OpenClaw alerts.

## Notes

- This project provides educational/decision support outputs.
- It does **not** execute trades automatically.
- Paper trading features are simulation-only and do **not** place real orders.
- Forecast features are scenario-based and do **not** guarantee future prices.

## Troubleshooting

- `ModuleNotFoundError` (for example `pandas`):
  activate your virtual environment and run `python -m pip install -r requirements.txt`.
- API returns `422` for query parameters:
  check ticker format and period format.
  Examples: `ticker=VOO`, `period=5y`, `period=1mo`, `period=max`.
- Frontend cannot reach backend:
  make sure backend is running on `http://127.0.0.1:8000` and frontend `.env`
  contains `VITE_API_BASE_URL=http://127.0.0.1:8000`.
- `No price data returned`:
  verify ticker symbol exists in Yahoo Finance and retry with another period.
- Running scripts from VS Code tasks:
  ensure `.venv312` exists and dependencies are installed in that environment.


## Chart Guide (Dashboard)

The dashboard charts are optimized for beginner readability:

- clear chart titles and ticker subtitles
- axis titles on every chart
- top legend with matching line colors
- hover tooltip with date + formatted values
- light gridlines for easier value reading
- built-in range selector (1M, 3M, 6M, 1Y, MAX)
- friendly fallback when data is missing: No data available

Axis meaning:

- Date: x-axis timeline
- Price (USD): price-level charts
- Return (%): model prediction vs actual outcome charts
- Volume: trading volume charts
- Score: scoring and oscillator charts
- Confidence (%): model confidence trend charts
- Portfolio Value (USD): virtual trader equity charts

How to read prediction vs actual:

- Prediction line = model output from walk-forward evaluation
- Actual line = realized future outcome for the same horizon
- Prediction Confidence chart = model confidence trend over time
- If prediction and actual frequently move together and rolling hit rate is stable, model behavior is more consistent
- Treat all outputs as decision-support signals, not guaranteed results

## Web Model Evaluation And Monthly Contributions

The web settings page now lets you configure two shared simulation inputs:

- `Model Evaluation¡]¼Ò«¬µû¦ô¡^`
  choose the active trained model for the web model-evaluation pages and virtual-trader pages
- `Monthly Contribution Records¡]¨C¤ëª`¸ê¬ö¿ý¡^`
  edit the available money for each month in USD

How model selection works:

- Open the dashboard settings page
- In `Model Evaluation¡]¼Ò«¬µû¦ô¡^`, choose a saved model such as:
  - `Logistic Regression`
  - `Random Forest`
  - `Gradient Boosting`
- The selected model is stored in backend SQLite and reused after reloads
- The current selected model is shown in both the Model Evaluation page and the Virtual Trader page

How monthly contribution records work:

- Records always start from `2026-04` (April 2026)
- If no records exist yet, the backend initializes them automatically from April 2026 through the current month
- You can edit each month independently, for example:
  - `2026-04: 1000`
  - `2026-05: 1500`
  - `2026-06: 800`
- Amounts are user-editable and are not fixed at 1000 USD
- A value of `0` means no contribution is added for that month

How the virtual trader uses these records:

- When the web UI requests virtual-trader results with a `user_id`, the backend uses the saved monthly contribution records for that user
- This replaces the old fixed monthly injection assumption for the web simulation flow
- Equity curve, monthly contribution history, and benchmark comparison now reflect those saved monthly amounts

New backend endpoints:

- `GET /model-evaluation/settings?user_id=...`
- `POST /model-evaluation/settings`
- `GET /monthly-contributions?user_id=...`
- `POST /monthly-contributions/initialize`
- `POST /monthly-contributions/update`

## Live Virtual Trader Mode

The project now supports two different trader views:

- Historical replay mode:
  uses saved walk-forward evaluation history for research comparison
- Live virtual trader mode:
  uses latest available market data and the selected saved model to decide
  simulated `buy`, `sell`, `hold`, or `no_action` now

Monthly contribution behavior in live mode:

- Contributions still start from `2026-04`
- When you save monthly records, each month is applied from that month onward
- If current month has an amount set, it becomes available immediately
- Duplicate runs in the same month do not double-count contributions
- If a month amount increases later, only the difference is applied

Live virtual trader endpoints:

- `GET /virtual-trader/live-status?user_id=...`
- `POST /virtual-trader/run-now`
- `GET /virtual-trader/live-trades?user_id=...`

News sentiment pipeline and debugging:

- News is fetched from Yahoo provider metadata, scored (FinBERT with lexicon fallback),
  then aggregated to daily and recent-7-day features
- New debug endpoints:
  - `GET /news-sentiment/latest?ticker=VOO`
  - `GET /news-sentiment/debug?ticker=VOO&date=2026-04-01`
- These endpoints help separate:
  - no recent matched news
  - fetched but unmatched-by-date window
  - pipeline/fetch failures

## Immutable Virtual Account Ledger

The live simulator now uses an append-only account ledger as source-of-truth.

- Historical cash/trade events are immutable (no in-place edits)
- Account state is rebuilt from ledger history
- Corrections should be compensating events (new deposit/withdrawal/trade event)

Ledger event types:

- `monthly_contribution`
- `manual_deposit`
- `withdrawal`
- `buy_trade`
- `sell_trade`
- `fee` (reserved)

Monthly contribution lock behavior:

- Start month is `2026-04`
- Create monthly contributions with `POST /monthly-contributions/create`
- Once a month is created, it is locked and cannot be overwritten
- Additional cash must be recorded separately via deposit/withdrawal events

Virtual account APIs:

- `GET /virtual-account/summary?user_id=...`
- `GET /virtual-account/ledger?user_id=...`
- `POST /virtual-account/deposit`
- `POST /virtual-account/withdraw`

Live trader + account APIs:

- `POST /virtual-trader/run-now`
- `GET /virtual-trader/status?user_id=...`
- `GET /virtual-trader/decisions?user_id=...`
- `GET /virtual-trader/trades?user_id=...`
- `GET /market-data/live-snapshot?ticker=VOO`

Data freshness note:

- Market/news are near-live snapshots from latest available provider data
- This project does not claim exchange-grade true real-time streaming

Continuous local runner:

```powershell
.venv\Scripts\python scripts\live_trader_runner.py --once --user-id demo-user
.venv\Scripts\python scripts\live_trader_runner.py --interval-seconds 300
```

## Trader Scheduler (Auto-Run)

The backend now starts a background trader scheduler automatically at app startup.

Cadence rules:
- Market open (U.S. ET 9:30-16:00, weekdays): every 5 minutes
- Market closed (including weekends): every 1 hour

Key endpoints:
- GET /virtual-trader/scheduler-status
- GET /trader-status (alias)
- POST /virtual-trader/scheduler-run-now

The scheduler and manual run-now share the same lock to prevent overlapping execution.
