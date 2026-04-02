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
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

When the server starts, open:

- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Run Backend + Frontend Together

Use two terminals in VS Code.

Terminal 1 (backend):

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
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

- Settings are stored locally in JSON at `USER_SETTINGS_PATH`
- Settings are saved per Discord user ID
- If a user has no saved settings, the bot uses sensible defaults
- Per-user language overrides the global `REPLY_LANGUAGE` default

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

How settings affect replies:

- `language`
  controls which action summary and explanation bullets are used
- `compact_mode`
  shortens `!analyze`, `!forecast`, and `!watchlist` output
- `default_watchlist`
  is used automatically by `!watchlist`; if empty, the bot falls back to the system default watchlist

Resetting settings:

- Use `!resetsettings` to clear your saved preferences and return to defaults

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
- Only hypothetical “would buy / would sell” events

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
```

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
  activate your virtual environment and run `pip install -r requirements.txt`.
- API returns `422` for query parameters:
  check ticker format and period format.
  Examples: `ticker=VOO`, `period=5y`, `period=1mo`, `period=max`.
- Frontend cannot reach backend:
  make sure backend is running on `http://127.0.0.1:8000` and frontend `.env`
  contains `VITE_API_BASE_URL=http://127.0.0.1:8000`.
- `No price data returned`:
  verify ticker symbol exists in Yahoo Finance and retry with another period.
- Running scripts from VS Code tasks:
  ensure `.venv` exists and dependencies are installed in that environment.
