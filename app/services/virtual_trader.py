"""Virtual trader simulation driven by model walk-forward predictions.

This module is simulation-only:
- no broker connectivity
- no leverage
- no real-money execution

The goal is to answer a practical research question:
"If we contributed cash monthly and only acted on out-of-sample model predictions,
would the strategy have made or lost money over time?"
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.settings import get_settings
from app.services.market_data import get_price_history
from app.services.research_pipeline import build_feature_dataset

logger = logging.getLogger(__name__)


class VirtualTraderError(Exception):
    """Raised when virtual trader inputs or state are invalid."""


@dataclass(frozen=True)
class VirtualTradeLogEntry:
    """One simulated trade-side event in the account timeline."""

    timestamp: str
    ticker: str
    action: str
    price: float
    quantity: float
    cash_after: float
    holdings_after: float
    entry_price: float | None
    exit_price: float | None
    position_size_value: float
    realized_pnl: float
    unrealized_pnl: float
    trade_reason: str


@dataclass(frozen=True)
class MonthlyContributionRecord:
    """One monthly contribution record."""

    date: str
    amount: float
    cumulative_contributions: float


@dataclass(frozen=True)
class EquityCurvePoint:
    """One daily account value point for charting."""

    date: str
    cash: float
    holdings_value: float
    total_equity: float
    realized_pnl: float
    unrealized_pnl: float
    benchmark_equity: float


@dataclass(frozen=True)
class VirtualTraderArtifact:
    """Saved artifact paths for one virtual trader run."""

    ticker: str
    period: str
    model_name: str
    summary_path: Path
    trade_log_path: Path
    equity_curve_path: Path
    contribution_history_path: Path
    benchmark_comparison_path: Path


@dataclass(frozen=True)
class VirtualTraderResult:
    """Structured simulation result."""

    ticker: str
    period: str
    model_name: str
    summary: dict[str, Any]
    benchmark_comparison: dict[str, Any]
    trade_log: list[VirtualTradeLogEntry]
    equity_curve: list[EquityCurvePoint]
    contribution_history: list[MonthlyContributionRecord]
    artifact: VirtualTraderArtifact


def _validate_price_columns(df: pd.DataFrame) -> None:
    """Validate the minimum columns needed for account simulation."""
    required = ["date", "close"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise VirtualTraderError(f"Missing required price columns: {missing}")


def _validate_evaluation_columns(df: pd.DataFrame) -> None:
    """Validate required walk-forward evaluation fields."""
    required = ["prediction_date", "ticker", "predicted_value", "actual_future_result"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise VirtualTraderError(f"Missing required evaluation columns: {missing}")


def _prepare_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize price data into a sorted daily frame."""
    _validate_price_columns(df)
    result = df.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    result = result.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    if result.empty:
        raise VirtualTraderError("Price history is empty after date cleaning.")
    return result


def _prepare_evaluation_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize the walk-forward evaluation table used as trading signals."""
    _validate_evaluation_columns(df)
    result = df.copy()
    result["prediction_date"] = pd.to_datetime(result["prediction_date"], errors="coerce")
    result = result.dropna(subset=["prediction_date"]).sort_values("prediction_date").reset_index(drop=True)
    if result.empty:
        raise VirtualTraderError("Evaluation table is empty after date cleaning.")
    return result.drop_duplicates(subset=["prediction_date"], keep="last")


def _align_benchmark_to_dates(
    benchmark_df: pd.DataFrame,
    target_dates: pd.Series,
) -> pd.DataFrame:
    """Align benchmark close prices to the simulation calendar."""
    benchmark_prices = _prepare_price_frame(benchmark_df)[["date", "close"]].rename(
        columns={"close": "benchmark_close"}
    )
    aligned = pd.DataFrame({"date": pd.to_datetime(target_dates)}).merge(
        benchmark_prices,
        on="date",
        how="left",
    )
    aligned["benchmark_close"] = aligned["benchmark_close"].ffill().bfill()
    return aligned


def _is_first_trading_day_of_month(current_date: pd.Timestamp, previous_date: pd.Timestamp | None) -> bool:
    """Treat the first available market date in a month as the contribution date."""
    if previous_date is None:
        return True
    return (current_date.year, current_date.month) != (previous_date.year, previous_date.month)


def _is_bullish_signal(row: pd.Series, task_type: str, min_predicted_return_pct: float) -> bool:
    """Interpret model output into a simple buy-or-not signal."""
    if task_type == "classification":
        return int(row["predicted_value"]) == 1
    return float(row["predicted_value"]) >= min_predicted_return_pct


def _is_bearish_signal(row: pd.Series, task_type: str) -> bool:
    """Interpret model output into a simple sell-or-not signal."""
    if task_type == "classification":
        return int(row["predicted_value"]) == 0
    return float(row["predicted_value"]) <= 0.0


def _passes_confidence_threshold(row: pd.Series, confidence_threshold: float) -> bool:
    """Allow entries/exits only when confidence is present and strong enough."""
    confidence = row.get("confidence_score")
    if confidence is None or pd.isna(confidence):
        return True
    return float(confidence) >= confidence_threshold


def _json_write(path: Path, payload: Any) -> None:
    """Write JSON with a consistent beginner-friendly format."""
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _save_virtual_trader_artifacts(
    ticker: str,
    period: str,
    model_name: str,
    summary: dict[str, Any],
    benchmark_comparison: dict[str, Any],
    trade_log: list[VirtualTradeLogEntry],
    equity_curve: list[EquityCurvePoint],
    contribution_history: list[MonthlyContributionRecord],
    output_dir: str | Path | None = None,
) -> VirtualTraderArtifact:
    """Save simulation outputs for later review and charting."""
    base_dir = Path(output_dir or get_settings().research_models_dir)
    artifact_dir = base_dir / ticker / period / "virtual_trader" / model_name
    artifact_dir.mkdir(parents=True, exist_ok=True)

    summary_path = artifact_dir / "summary.json"
    trade_log_path = artifact_dir / "trade_log.csv"
    equity_curve_path = artifact_dir / "equity_curve.csv"
    contribution_history_path = artifact_dir / "monthly_contributions.csv"
    benchmark_comparison_path = artifact_dir / "benchmark_comparison.json"

    _json_write(summary_path, summary)
    _json_write(benchmark_comparison_path, benchmark_comparison)
    pd.DataFrame([item.__dict__ for item in trade_log]).to_csv(trade_log_path, index=False)
    pd.DataFrame([item.__dict__ for item in equity_curve]).to_csv(equity_curve_path, index=False)
    pd.DataFrame([item.__dict__ for item in contribution_history]).to_csv(
        contribution_history_path,
        index=False,
    )

    return VirtualTraderArtifact(
        ticker=ticker,
        period=period,
        model_name=model_name,
        summary_path=summary_path,
        trade_log_path=trade_log_path,
        equity_curve_path=equity_curve_path,
        contribution_history_path=contribution_history_path,
        benchmark_comparison_path=benchmark_comparison_path,
    )


def simulate_virtual_trader(
    ticker: str,
    period: str,
    model_name: str,
    price_df: pd.DataFrame,
    evaluation_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    benchmark_symbol: str = "VOO",
    monthly_contribution_usd: float = 1_000.0,
    initial_cash: float = 0.0,
    confidence_threshold: float = 0.55,
    max_position_size_pct: float = 0.25,
    stop_loss_pct: float = 0.10,
    take_profit_pct: float | None = None,
    task_type: str = "classification",
    min_predicted_return_pct: float = 0.0,
    output_dir: str | Path | None = None,
) -> VirtualTraderResult:
    """Run a transparent no-leverage virtual trader simulation.

    Important:
    - We only use walk-forward, out-of-sample predictions as trading signals.
    - No leverage is allowed: position size is always capped by available cash.
    - Monthly contributions are added on the first trading day of each month.
    """
    if monthly_contribution_usd < 0:
        raise VirtualTraderError("monthly_contribution_usd must be >= 0.")
    if initial_cash < 0:
        raise VirtualTraderError("initial_cash must be >= 0.")
    if not 0 < max_position_size_pct <= 1:
        raise VirtualTraderError("max_position_size_pct must be within (0, 1].")
    if stop_loss_pct < 0:
        raise VirtualTraderError("stop_loss_pct must be >= 0.")
    if take_profit_pct is not None and take_profit_pct <= 0:
        raise VirtualTraderError("take_profit_pct must be > 0 when provided.")
    if not 0 <= confidence_threshold <= 1:
        raise VirtualTraderError("confidence_threshold must be between 0 and 1.")

    ticker_symbol = ticker.strip().upper()
    benchmark_symbol = benchmark_symbol.strip().upper()
    price_work_df = _prepare_price_frame(price_df)
    eval_work_df = _prepare_evaluation_frame(evaluation_df)
    aligned_benchmark_df = _align_benchmark_to_dates(benchmark_df, price_work_df["date"])
    work_df = price_work_df.merge(aligned_benchmark_df, on="date", how="left")

    signal_by_date = {
        row["prediction_date"].strftime("%Y-%m-%d"): row
        for _, row in eval_work_df.iterrows()
    }

    cash = float(initial_cash)
    shares = 0.0
    avg_entry_price: float | None = None
    realized_pnl = 0.0
    total_contributions = float(initial_cash)

    benchmark_cash = float(initial_cash)
    benchmark_shares = 0.0

    trade_log: list[VirtualTradeLogEntry] = []
    contribution_history: list[MonthlyContributionRecord] = []
    equity_curve: list[EquityCurvePoint] = []

    previous_date: pd.Timestamp | None = None

    logger.info(
        "Running virtual trader ticker=%s model=%s period=%s rows=%d",
        ticker_symbol,
        model_name,
        period,
        len(work_df),
    )

    for _, row in work_df.iterrows():
        current_date = pd.to_datetime(row["date"])
        date_str = current_date.strftime("%Y-%m-%d")
        close_price = float(row["close"])
        benchmark_close = float(row["benchmark_close"])

        if _is_first_trading_day_of_month(current_date, previous_date):
            cash += monthly_contribution_usd
            benchmark_cash += monthly_contribution_usd
            total_contributions += monthly_contribution_usd
            contribution_history.append(
                MonthlyContributionRecord(
                    date=date_str,
                    amount=float(monthly_contribution_usd),
                    cumulative_contributions=float(total_contributions),
                )
            )

        if benchmark_close > 0 and benchmark_cash > 0:
            benchmark_shares += benchmark_cash / benchmark_close
            benchmark_cash = 0.0

        holdings_value_before = shares * close_price
        total_equity_before = cash + holdings_value_before

        signal_row = signal_by_date.get(date_str)
        should_exit = False
        exit_reason = ""

        if shares > 0 and avg_entry_price is not None:
            if stop_loss_pct > 0 and close_price <= avg_entry_price * (1 - stop_loss_pct):
                should_exit = True
                exit_reason = "stop_loss"
            elif take_profit_pct is not None and close_price >= avg_entry_price * (1 + take_profit_pct):
                should_exit = True
                exit_reason = "take_profit"
            elif signal_row is not None and _passes_confidence_threshold(signal_row, confidence_threshold):
                if _is_bearish_signal(signal_row, task_type=task_type):
                    should_exit = True
                    exit_reason = "model_bearish_signal"

        if should_exit and shares > 0:
            sale_value = shares * close_price
            trade_realized_pnl = (close_price - float(avg_entry_price)) * shares if avg_entry_price else 0.0
            cash += sale_value
            realized_pnl += trade_realized_pnl

            trade_log.append(
                VirtualTradeLogEntry(
                    timestamp=date_str,
                    ticker=ticker_symbol,
                    action="sell",
                    price=float(close_price),
                    quantity=float(shares),
                    cash_after=float(cash),
                    holdings_after=0.0,
                    entry_price=float(avg_entry_price) if avg_entry_price is not None else None,
                    exit_price=float(close_price),
                    position_size_value=0.0,
                    realized_pnl=float(realized_pnl),
                    unrealized_pnl=0.0,
                    trade_reason=exit_reason,
                )
            )
            shares = 0.0
            avg_entry_price = None

        holdings_value_after_exit = shares * close_price
        total_equity_after_exit = cash + holdings_value_after_exit

        can_enter = (
            shares == 0
            and signal_row is not None
            and _passes_confidence_threshold(signal_row, confidence_threshold)
            and _is_bullish_signal(signal_row, task_type=task_type, min_predicted_return_pct=min_predicted_return_pct)
        )

        if can_enter and close_price > 0:
            max_position_value = total_equity_after_exit * max_position_size_pct
            buy_value = min(cash, max_position_value)

            if buy_value > 0:
                buy_shares = buy_value / close_price
                shares = float(buy_shares)
                cash -= buy_value
                avg_entry_price = float(close_price)
                unrealized_pnl = 0.0

                trade_log.append(
                    VirtualTradeLogEntry(
                        timestamp=date_str,
                        ticker=ticker_symbol,
                        action="buy",
                        price=float(close_price),
                        quantity=float(shares),
                        cash_after=float(cash),
                        holdings_after=float(shares),
                        entry_price=float(avg_entry_price),
                        exit_price=None,
                        position_size_value=float(shares * close_price),
                        realized_pnl=float(realized_pnl),
                        unrealized_pnl=float(unrealized_pnl),
                        trade_reason="model_bullish_signal",
                    )
                )

        holdings_value = shares * close_price
        unrealized_pnl = 0.0 if shares == 0 or avg_entry_price is None else (close_price - avg_entry_price) * shares
        total_equity = cash + holdings_value
        benchmark_equity = benchmark_cash + benchmark_shares * benchmark_close

        equity_curve.append(
            EquityCurvePoint(
                date=date_str,
                cash=float(cash),
                holdings_value=float(holdings_value),
                total_equity=float(total_equity),
                realized_pnl=float(realized_pnl),
                unrealized_pnl=float(unrealized_pnl),
                benchmark_equity=float(benchmark_equity),
            )
        )

        previous_date = current_date

    if not equity_curve:
        raise VirtualTraderError("Simulation produced no equity curve points.")

    final_equity = equity_curve[-1].total_equity
    benchmark_final_equity = equity_curve[-1].benchmark_equity
    unrealized_pnl = equity_curve[-1].unrealized_pnl

    benchmark_comparison = {
        "benchmark": benchmark_symbol,
        "final_equity": float(benchmark_final_equity),
        "total_contributions": float(total_contributions),
        "return_on_contributions_pct": (
            float((benchmark_final_equity / total_contributions - 1) * 100) if total_contributions > 0 else 0.0
        ),
    }

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "ticker": ticker_symbol,
        "period": period,
        "model_name": model_name,
        "mode": "simulation_only_no_real_money_no_leverage",
        "task_type": task_type,
        "monthly_contribution_usd": float(monthly_contribution_usd),
        "initial_cash": float(initial_cash),
        "confidence_threshold": float(confidence_threshold),
        "max_position_size_pct": float(max_position_size_pct),
        "stop_loss_pct": float(stop_loss_pct),
        "take_profit_pct": float(take_profit_pct) if take_profit_pct is not None else None,
        "total_contributions": float(total_contributions),
        "cash": float(cash),
        "holdings": float(shares),
        "entry_price": float(avg_entry_price) if avg_entry_price is not None else None,
        "exit_price": None,
        "realized_pnl": float(realized_pnl),
        "unrealized_pnl": float(unrealized_pnl),
        "final_equity": float(final_equity),
        "return_on_contributions_pct": (
            float((final_equity / total_contributions - 1) * 100) if total_contributions > 0 else 0.0
        ),
        "trade_count": int(len(trade_log)),
        "benchmark_symbol": benchmark_symbol,
        "benchmark_final_equity": float(benchmark_final_equity),
        "outperformance_vs_benchmark_pct_points": (
            float((final_equity / total_contributions - benchmark_final_equity / total_contributions) * 100)
            if total_contributions > 0
            else 0.0
        ),
    }

    artifact = _save_virtual_trader_artifacts(
        ticker=ticker_symbol,
        period=period,
        model_name=model_name,
        summary=summary,
        benchmark_comparison=benchmark_comparison,
        trade_log=trade_log,
        equity_curve=equity_curve,
        contribution_history=contribution_history,
        output_dir=output_dir,
    )

    return VirtualTraderResult(
        ticker=ticker_symbol,
        period=period,
        model_name=model_name,
        summary=summary,
        benchmark_comparison=benchmark_comparison,
        trade_log=trade_log,
        equity_curve=equity_curve,
        contribution_history=contribution_history,
        artifact=artifact,
    )


def run_virtual_trader_from_model(
    ticker: str,
    period: str = "5y",
    benchmark: str = "VOO",
    target_name: str = "target_5d_updown",
    task_type: str = "classification",
    model_name: str = "logistic_regression",
    monthly_contribution_usd: float = 1_000.0,
    initial_cash: float = 0.0,
    confidence_threshold: float = 0.55,
    max_position_size_pct: float = 0.25,
    stop_loss_pct: float = 0.10,
    take_profit_pct: float | None = None,
    min_predicted_return_pct: float = 0.0,
    include_news_sentiment: bool = True,
    sentiment_model: str = "finbert",
    output_dir: str | Path | None = None,
) -> VirtualTraderResult:
    """Train one baseline model, then simulate trading from walk-forward predictions."""
    from app.services.model_training import train_baseline_model  # local import keeps this module usable without sklearn

    ticker_symbol = ticker.strip().upper()
    benchmark_symbol = benchmark.strip().upper()

    dataset_df = build_feature_dataset(
        ticker=ticker_symbol,
        period=period,
        benchmark=benchmark_symbol,
        include_news_sentiment=include_news_sentiment,
        sentiment_model=sentiment_model,
    )
    training_result = train_baseline_model(
        dataset_df=dataset_df,
        ticker=ticker_symbol,
        period=period,
        target_name=target_name,
        task_type=task_type,
        model_name=model_name,
        output_dir=output_dir,
    )
    price_df = dataset_df[["date", "close"]].copy()
    benchmark_df = get_price_history(benchmark_symbol, period=period)

    return simulate_virtual_trader(
        ticker=ticker_symbol,
        period=period,
        model_name=model_name,
        price_df=price_df,
        evaluation_df=training_result.evaluation_table,
        benchmark_df=benchmark_df,
        benchmark_symbol=benchmark_symbol,
        monthly_contribution_usd=monthly_contribution_usd,
        initial_cash=initial_cash,
        confidence_threshold=confidence_threshold,
        max_position_size_pct=max_position_size_pct,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        task_type=task_type,
        min_predicted_return_pct=min_predicted_return_pct,
        output_dir=output_dir,
    )
