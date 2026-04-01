"""Simple, explainable backtesting engine for the scoring strategy."""

from __future__ import annotations

from dataclasses import dataclass
import logging

import pandas as pd

logger = logging.getLogger(__name__)


class BacktestInputError(Exception):
    """Raised when input data for backtesting is invalid."""


@dataclass(frozen=True)
class BacktestTrade:
    """One completed trade record."""

    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    return_pct: float
    exit_reason: str


@dataclass(frozen=True)
class BacktestResult:
    """Backtest output payload."""

    metrics: dict[str, float | int]
    trades: list[BacktestTrade]
    equity_curve: list[dict[str, float | str]]


def _validate_columns(df: pd.DataFrame) -> None:
    """Validate minimum required columns for this strategy."""
    required = ["date", "close", "sma_50", "sma_200", "rsi_14", "macd_line", "macd_signal"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise BacktestInputError(f"Missing required columns for backtest: {missing}")


def _max_drawdown_pct(equity_series: pd.Series) -> float:
    """Calculate max drawdown percent from an equity curve series."""
    rolling_peak = equity_series.cummax()
    drawdown = (equity_series - rolling_peak) / rolling_peak
    return float(drawdown.min() * 100)


def _is_entry_signal(row: pd.Series) -> bool:
    """Entry rule: trend + momentum confirmation."""
    return (
        (row["close"] > row["sma_200"])
        and (row["sma_50"] > row["sma_200"])
        and (45 <= row["rsi_14"] <= 65)
        and (row["macd_line"] > row["macd_signal"])
    )


def _has_bearish_macd_crossover(prev_row: pd.Series, row: pd.Series) -> bool:
    """Exit trigger when MACD crosses from bullish to bearish."""
    return (prev_row["macd_line"] >= prev_row["macd_signal"]) and (
        row["macd_line"] < row["macd_signal"]
    )


def run_backtest(
    df: pd.DataFrame,
    transaction_cost_pct: float = 0.0,
) -> BacktestResult:
    """
    Run a simple long-only daily backtest.

    Rules:
    - Enter when close > SMA200, SMA50 > SMA200, RSI in [45, 65], and MACD bullish.
    - Exit when close < SMA200 OR bearish MACD crossover.
    - One position at a time.
    """
    if transaction_cost_pct < 0:
        raise BacktestInputError("transaction_cost_pct must be >= 0.")
    if df.empty:
        raise BacktestInputError("Cannot backtest empty DataFrame.")

    logger.info(
        "Running backtest with rows=%d transaction_cost_pct=%s",
        len(df),
        transaction_cost_pct,
    )

    _validate_columns(df)
    work_df = df.copy().reset_index(drop=True)
    work_df["date"] = pd.to_datetime(work_df["date"], errors="coerce")
    work_df = work_df.dropna(subset=["date"]).reset_index(drop=True)
    if work_df.empty:
        raise BacktestInputError("No valid date rows after cleaning backtest input.")

    initial_equity = 1.0
    cash = initial_equity
    shares = 0.0
    in_position = False

    entry_date: str | None = None
    entry_price: float | None = None

    trades: list[BacktestTrade] = []
    equity_curve: list[dict[str, float | str]] = []

    for index in range(len(work_df)):
        row = work_df.iloc[index]
        close_price = float(row["close"])
        date_str = row["date"].strftime("%Y-%m-%d")

        if index == 0:
            prev_row = row
        else:
            prev_row = work_df.iloc[index - 1]

        # Skip rows where indicators are not fully available.
        has_required_values = pd.notna(row["sma_50"]) and pd.notna(row["sma_200"]) and pd.notna(
            row["rsi_14"]
        ) and pd.notna(row["macd_line"]) and pd.notna(row["macd_signal"])
        if not has_required_values:
            equity_curve.append({"date": date_str, "equity": float(cash + shares * close_price)})
            continue

        # Exit first, then evaluate new entries after position is flat.
        if in_position:
            exit_due_to_trend = close_price < float(row["sma_200"])
            exit_due_to_macd = _has_bearish_macd_crossover(prev_row, row)

            if exit_due_to_trend or exit_due_to_macd:
                cash = shares * close_price * (1 - transaction_cost_pct)
                shares = 0.0
                in_position = False

                if entry_price is None or entry_date is None:
                    raise BacktestInputError("Trade state corrupted: missing entry info.")

                trade_return_pct = (
                    ((close_price * (1 - transaction_cost_pct)) / (entry_price * (1 + transaction_cost_pct)) - 1)
                    * 100
                )
                trades.append(
                    BacktestTrade(
                        entry_date=entry_date,
                        entry_price=float(entry_price),
                        exit_date=date_str,
                        exit_price=close_price,
                        return_pct=float(trade_return_pct),
                        exit_reason="close_below_sma200" if exit_due_to_trend else "macd_bearish_crossover",
                    )
                )

                entry_date = None
                entry_price = None

        if not in_position and _is_entry_signal(row):
            entry_fill_price = close_price * (1 + transaction_cost_pct)
            shares = cash / entry_fill_price
            cash = 0.0
            in_position = True
            entry_date = date_str
            entry_price = close_price

        equity = cash + shares * close_price
        equity_curve.append({"date": date_str, "equity": float(equity)})

    # Force close any open position at the last available close.
    if in_position:
        last_row = work_df.iloc[-1]
        close_price = float(last_row["close"])
        date_str = last_row["date"].strftime("%Y-%m-%d")
        cash = shares * close_price * (1 - transaction_cost_pct)
        shares = 0.0
        in_position = False

        if entry_price is None or entry_date is None:
            raise BacktestInputError("Trade state corrupted on forced close.")

        trade_return_pct = (
            ((close_price * (1 - transaction_cost_pct)) / (entry_price * (1 + transaction_cost_pct)) - 1)
            * 100
        )
        trades.append(
            BacktestTrade(
                entry_date=entry_date,
                entry_price=float(entry_price),
                exit_date=date_str,
                exit_price=close_price,
                return_pct=float(trade_return_pct),
                exit_reason="end_of_data",
            )
        )

        equity_curve[-1] = {"date": date_str, "equity": float(cash)}

    equity_df = pd.DataFrame(equity_curve)
    final_equity = float(equity_df.iloc[-1]["equity"])
    total_return_pct = (final_equity / initial_equity - 1) * 100

    start_date = pd.to_datetime(work_df.iloc[0]["date"])
    end_date = pd.to_datetime(work_df.iloc[-1]["date"])
    elapsed_years = max((end_date - start_date).days / 365.25, 1 / 365.25)
    cagr_pct = ((final_equity / initial_equity) ** (1 / elapsed_years) - 1) * 100

    max_drawdown_pct = _max_drawdown_pct(equity_df["equity"])

    num_trades = len(trades)
    win_rate_pct = (
        (sum(1 for trade in trades if trade.return_pct > 0) / num_trades) * 100 if num_trades else 0.0
    )
    avg_trade_return_pct = (
        sum(trade.return_pct for trade in trades) / num_trades if num_trades else 0.0
    )

    first_close = float(work_df.iloc[0]["close"])
    last_close = float(work_df.iloc[-1]["close"])
    buy_and_hold_return_pct = ((last_close / first_close) - 1) * 100

    metrics = {
        "total_return_pct": float(total_return_pct),
        "cagr_pct": float(cagr_pct),
        "max_drawdown_pct": float(max_drawdown_pct),
        "win_rate_pct": float(win_rate_pct),
        "number_of_trades": int(num_trades),
        "average_trade_return_pct": float(avg_trade_return_pct),
        "buy_and_hold_return_pct": float(buy_and_hold_return_pct),
        "transaction_cost_pct": float(transaction_cost_pct),
    }

    logger.info(
        "Backtest complete: trades=%d total_return_pct=%.2f cagr_pct=%.2f",
        num_trades,
        total_return_pct,
        cagr_pct,
    )
    return BacktestResult(metrics=metrics, trades=trades, equity_curve=equity_curve)
