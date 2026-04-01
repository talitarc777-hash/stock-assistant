"""Paper-trading simulation only.

This module is strictly for simulated educational workflows:
- No broker connectivity
- No real-money execution
- No auto-trading
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

import pandas as pd


logger = logging.getLogger(__name__)


class PaperSimulationError(Exception):
    """Raised when paper simulation input is invalid."""


@dataclass(frozen=True)
class PaperEvent:
    """One simulated event in timeline."""

    date: str
    event: str
    price: float
    quantity: float
    cash_after: float
    position_after: float
    realized_pnl: float
    note: str


@dataclass(frozen=True)
class PaperSimulationResult:
    """Paper simulation output payload."""

    ticker: str
    initial_cash: float
    cash: float
    position_qty: float
    position_market_value: float
    total_equity: float
    avg_entry_price: float | None
    realized_pnl: float
    unrealized_pnl: float
    events: list[PaperEvent]


def _validate_columns(df: pd.DataFrame) -> None:
    """Validate required columns used by simulation signal logic."""
    required = ["date", "close", "sma_50", "sma_200", "rsi_14", "macd_line", "macd_signal"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise PaperSimulationError(f"Missing required columns for paper simulation: {missing}")


def _is_entry_signal(row: pd.Series) -> bool:
    """Use the same entry logic as backtest (would-buy signal)."""
    return (
        (row["close"] > row["sma_200"])
        and (row["sma_50"] > row["sma_200"])
        and (45 <= row["rsi_14"] <= 65)
        and (row["macd_line"] > row["macd_signal"])
    )


def _has_bearish_macd_crossover(previous_row: pd.Series, row: pd.Series) -> bool:
    """Use the same MACD bearish crossover logic as backtest (would-sell signal)."""
    return (previous_row["macd_line"] >= previous_row["macd_signal"]) and (
        row["macd_line"] < row["macd_signal"]
    )


def run_paper_simulation(
    ticker: str,
    indicators_df: pd.DataFrame,
    initial_cash: float = 10_000.0,
) -> PaperSimulationResult:
    """
    Run simulation-only strategy events over historical rows.

    Important:
    - This function does not execute any order in a market.
    - Events are hypothetical "would buy/sell" actions for learning/testing.
    """
    if initial_cash <= 0:
        raise PaperSimulationError("initial_cash must be > 0.")
    if indicators_df.empty:
        raise PaperSimulationError("Cannot simulate with empty data.")

    _validate_columns(indicators_df)
    work_df = indicators_df.copy().reset_index(drop=True)
    work_df["date"] = pd.to_datetime(work_df["date"], errors="coerce")
    work_df = work_df.dropna(subset=["date"]).reset_index(drop=True)
    if work_df.empty:
        raise PaperSimulationError("No valid date rows after cleaning input.")

    cash = float(initial_cash)
    position_qty = 0.0
    avg_entry_price: float | None = None
    realized_pnl = 0.0
    events: list[PaperEvent] = []

    logger.info("Running paper simulation for ticker=%s rows=%d", ticker, len(work_df))

    for index in range(len(work_df)):
        row = work_df.iloc[index]
        date_str = row["date"].strftime("%Y-%m-%d")
        close_price = float(row["close"])
        previous_row = work_df.iloc[index - 1] if index > 0 else row

        # Wait for indicators to become available.
        if any(pd.isna(row[col]) for col in ["sma_50", "sma_200", "rsi_14", "macd_line", "macd_signal"]):
            continue

        in_position = position_qty > 0
        should_exit = False
        exit_note = ""
        if in_position:
            if close_price < float(row["sma_200"]):
                should_exit = True
                exit_note = "would sell: close below SMA200"
            elif _has_bearish_macd_crossover(previous_row, row):
                should_exit = True
                exit_note = "would sell: MACD bearish crossover"

        if should_exit:
            sale_value = position_qty * close_price
            trade_pnl = 0.0
            if avg_entry_price is not None:
                trade_pnl = (close_price - avg_entry_price) * position_qty
            cash += sale_value
            realized_pnl += trade_pnl
            events.append(
                PaperEvent(
                    date=date_str,
                    event="would_sell",
                    price=close_price,
                    quantity=position_qty,
                    cash_after=float(cash),
                    position_after=0.0,
                    realized_pnl=float(realized_pnl),
                    note=exit_note,
                )
            )
            position_qty = 0.0
            avg_entry_price = None

        if position_qty == 0 and _is_entry_signal(row):
            buy_qty = cash / close_price
            position_qty = float(buy_qty)
            avg_entry_price = close_price
            cash = 0.0
            events.append(
                PaperEvent(
                    date=date_str,
                    event="would_buy",
                    price=close_price,
                    quantity=position_qty,
                    cash_after=0.0,
                    position_after=position_qty,
                    realized_pnl=float(realized_pnl),
                    note="would buy: trend+momentum entry signal",
                )
            )

    latest_close = float(work_df.iloc[-1]["close"])
    position_market_value = position_qty * latest_close
    total_equity = cash + position_market_value
    unrealized_pnl = 0.0
    if position_qty > 0 and avg_entry_price is not None:
        unrealized_pnl = (latest_close - avg_entry_price) * position_qty

    return PaperSimulationResult(
        ticker=ticker.strip().upper(),
        initial_cash=float(initial_cash),
        cash=float(cash),
        position_qty=float(position_qty),
        position_market_value=float(position_market_value),
        total_equity=float(total_equity),
        avg_entry_price=float(avg_entry_price) if avg_entry_price is not None else None,
        realized_pnl=float(realized_pnl),
        unrealized_pnl=float(unrealized_pnl),
        events=events,
    )

