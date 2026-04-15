"""Live virtual trader mode using latest model output and market data.

Simulation only:
- no broker execution
- no leverage
- no real-money trading
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import logging
from pathlib import Path
import sqlite3
from typing import Any

import pandas as pd

from app.core.settings import get_settings
from app.services.account_ledger_service import (
    AccountLedgerError,
    get_account_ledger_service,
)
from app.services.live_market_data_service import get_live_market_snapshot
from app.services.market_data import get_price_history
from app.services.model_results import ModelResultsError, load_trained_model_bundle
from app.services.prediction_explanations import build_prediction_explanation
from app.services.research_pipeline import build_feature_dataset
from app.services.user_profile_service import get_user_profile_store

logger = logging.getLogger(__name__)


class LiveVirtualTraderError(Exception):
    """Raised when live virtual trader inputs/state are invalid."""


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _normalize_tickers(tickers: list[str]) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for ticker in tickers:
        symbol = str(ticker).strip().upper()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        values.append(symbol)
    return values


@dataclass(frozen=True)
class LiveStatus:
    user_id: str
    model_name: str
    generated_at_utc: str
    account: dict[str, Any]
    holdings: list[dict[str, Any]]
    latest_decisions: list[dict[str, Any]]
    contribution_events: list[dict[str, Any]]


class LiveVirtualTraderStore:
    """SQLite persistence for live positions and action log."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = Path(db_path or get_settings().profile_db_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS live_trader_positions (
                    user_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    avg_entry_price REAL NOT NULL,
                    entry_timestamp TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, ticker)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS live_trader_trade_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    action TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    model_name TEXT NOT NULL,
                    confidence_score REAL,
                    reason TEXT NOT NULL,
                    threshold_summary TEXT NOT NULL,
                    technical_state_summary TEXT NOT NULL,
                    news_sentiment_summary TEXT NOT NULL,
                    benchmark_strength_summary TEXT NOT NULL,
                    action_summary TEXT NOT NULL,
                    cash_after REAL NOT NULL,
                    holdings_after REAL NOT NULL,
                    realized_pnl REAL NOT NULL,
                    unrealized_pnl REAL NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def list_positions(self, user_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM live_trader_positions
                WHERE user_id = ?
                ORDER BY ticker ASC
                """,
                (str(user_id).strip(),),
            ).fetchall()
        return [
            {
                "user_id": row["user_id"],
                "ticker": row["ticker"],
                "quantity": float(row["quantity"]),
                "avg_entry_price": float(row["avg_entry_price"]),
                "entry_timestamp": row["entry_timestamp"],
                "model_name": row["model_name"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def get_position(self, user_id: str, ticker: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM live_trader_positions
                WHERE user_id = ? AND ticker = ?
                """,
                (str(user_id).strip(), str(ticker).strip().upper()),
            ).fetchone()
        if row is None:
            return None
        return {
            "user_id": row["user_id"],
            "ticker": row["ticker"],
            "quantity": float(row["quantity"]),
            "avg_entry_price": float(row["avg_entry_price"]),
            "entry_timestamp": row["entry_timestamp"],
            "model_name": row["model_name"],
            "updated_at": row["updated_at"],
        }

    def upsert_position(
        self,
        user_id: str,
        ticker: str,
        quantity: float,
        avg_entry_price: float,
        model_name: str,
        entry_timestamp: str | None = None,
    ) -> None:
        now = _utc_now()
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT entry_timestamp FROM live_trader_positions WHERE user_id = ? AND ticker = ?",
                (str(user_id).strip(), str(ticker).strip().upper()),
            ).fetchone()
            first_entry = entry_timestamp or (existing["entry_timestamp"] if existing else now)
            conn.execute(
                """
                INSERT INTO live_trader_positions (
                    user_id, ticker, quantity, avg_entry_price, entry_timestamp, model_name, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, ticker) DO UPDATE SET
                    quantity = excluded.quantity,
                    avg_entry_price = excluded.avg_entry_price,
                    model_name = excluded.model_name,
                    updated_at = excluded.updated_at
                """,
                (
                    str(user_id).strip(),
                    str(ticker).strip().upper(),
                    float(quantity),
                    float(avg_entry_price),
                    first_entry,
                    str(model_name).strip().lower(),
                    now,
                ),
            )
            conn.commit()

    def remove_position(self, user_id: str, ticker: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM live_trader_positions WHERE user_id = ? AND ticker = ?",
                (str(user_id).strip(), str(ticker).strip().upper()),
            )
            conn.commit()

    def append_trade(self, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO live_trader_trade_log (
                    timestamp, user_id, ticker, action, quantity, price, model_name,
                    confidence_score, reason, threshold_summary, technical_state_summary,
                    news_sentiment_summary, benchmark_strength_summary, action_summary,
                    cash_after, holdings_after, realized_pnl, unrealized_pnl, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["timestamp"],
                    payload["user_id"],
                    payload["ticker"],
                    payload["action"],
                    float(payload["quantity"]),
                    float(payload["price"]),
                    payload["model_name"],
                    payload.get("confidence_score"),
                    payload["reason"],
                    payload["threshold_summary"],
                    payload["technical_state_summary"],
                    payload["news_sentiment_summary"],
                    payload["benchmark_strength_summary"],
                    payload["action_summary"],
                    float(payload["cash_after"]),
                    float(payload["holdings_after"]),
                    float(payload["realized_pnl"]),
                    float(payload["unrealized_pnl"]),
                    json.dumps(payload.get("metadata", {}), ensure_ascii=False),
                ),
            )
            conn.commit()

    def list_trades(self, user_id: str, limit: int = 50, ticker: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM live_trader_trade_log WHERE user_id = ?"
        params: list[Any] = [str(user_id).strip()]
        if ticker:
            sql += " AND ticker = ?"
            params.append(str(ticker).strip().upper())
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(max(1, int(limit)))
        with self._connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            try:
                metadata = json.loads(row["metadata_json"] or "{}")
            except json.JSONDecodeError:
                metadata = {}
            result.append(
                {
                    "timestamp": row["timestamp"],
                    "user_id": row["user_id"],
                    "ticker": row["ticker"],
                    "action": row["action"],
                    "quantity": float(row["quantity"]),
                    "price": float(row["price"]),
                    "model_name": row["model_name"],
                    "confidence_score": row["confidence_score"],
                    "reason": row["reason"],
                    "threshold_summary": row["threshold_summary"],
                    "technical_state_summary": row["technical_state_summary"],
                    "news_sentiment_summary": row["news_sentiment_summary"],
                    "benchmark_strength_summary": row["benchmark_strength_summary"],
                    "action_summary": row["action_summary"],
                    "cash_after": float(row["cash_after"]),
                    "holdings_after": float(row["holdings_after"]),
                    "realized_pnl": float(row["realized_pnl"]),
                    "unrealized_pnl": float(row["unrealized_pnl"]),
                    "metadata": metadata,
                }
            )
        return result


def _resolve_user_tickers(user_id: str, tickers: list[str] | None) -> list[str]:
    if tickers:
        values = _normalize_tickers(tickers)
        if values:
            return values
    watchlist, _, _ = get_user_profile_store().get_effective_watchlist(user_id=user_id)
    values = _normalize_tickers(watchlist)
    if not values:
        raise LiveVirtualTraderError("No tickers available for live virtual trader.")
    return values


def _confidence_ok(confidence_score: float | None, threshold: float) -> bool:
    return confidence_score is None or float(confidence_score) >= float(threshold)


def _derive_signal_flags(predicted_value: float, task_type: str, min_return: float) -> tuple[bool, bool]:
    if task_type == "classification":
        bullish = int(round(predicted_value)) == 1
        bearish = int(round(predicted_value)) == 0
    else:
        bullish = predicted_value >= min_return
        bearish = predicted_value <= 0.0
    return bullish, bearish


def _latest_prices_for_symbols(symbols: list[str]) -> dict[str, float]:
    prices: dict[str, float] = {}
    for symbol in symbols:
        history = get_price_history(symbol, period="3mo")
        prices[symbol] = float(history.sort_values("date").iloc[-1]["close"])
    return prices


def run_live_virtual_trader_now(
    user_id: str,
    tickers: list[str] | None = None,
    model_name: str = "logistic_regression",
    period: str = "2y",
    benchmark: str = "VOO",
    target_name: str = "target_5d_updown",
    confidence_threshold: float = 0.55,
    max_position_size_pct: float = 0.25,
    stop_loss_pct: float = 0.10,
    take_profit_pct: float | None = None,
    min_predicted_return_pct: float = 0.0,
) -> LiveStatus:
    """Run one live decision cycle and persist simulated actions."""
    clean_user_id = str(user_id).strip()
    if not clean_user_id:
        raise LiveVirtualTraderError("user_id is required.")
    if not 0 < max_position_size_pct <= 1:
        raise LiveVirtualTraderError("max_position_size_pct must be within (0, 1].")

    symbols = _resolve_user_tickers(clean_user_id, tickers)
    ledger = get_account_ledger_service()
    store = get_live_virtual_trader_store()
    contribution_events = ledger.list_events(
        clean_user_id,
        limit=24,
        event_types=["monthly_contribution", "manual_deposit", "withdrawal"],
    )

    decisions: list[dict[str, Any]] = []
    latest_row_cache: dict[str, pd.Series] = {}
    latest_price_cache: dict[str, float] = {}
    valuation_cache: dict[str, dict[str, Any]] = {}

    for symbol in symbols:
        feature_df = build_feature_dataset(
            ticker=symbol,
            period=period,
            benchmark=benchmark,
            include_news_sentiment=True,
            sentiment_model="finbert",
        ).sort_values("date")
        if feature_df.empty:
            continue
        latest_row = feature_df.iloc[-1]
        latest_row_cache[symbol] = latest_row
        latest_price_cache[symbol] = float(latest_row["close"])
        snapshot = get_live_market_snapshot(symbol, period="3mo")
        valuation_cache[symbol] = snapshot
        latest_price_cache[symbol] = float(snapshot["close"])

    account = ledger.build_account_summary(clean_user_id, latest_prices=latest_price_cache)
    held_positions = account["holdings"]
    extra_symbols = [item["ticker"] for item in held_positions if item["ticker"] not in latest_price_cache]
    if extra_symbols:
        latest_price_cache.update(_latest_prices_for_symbols(extra_symbols))
        account = ledger.build_account_summary(clean_user_id, latest_prices=latest_price_cache)

    holdings_by_ticker = {item["ticker"]: item for item in account["holdings"]}

    for symbol in symbols:
        latest_row = latest_row_cache.get(symbol)
        if latest_row is None:
            continue
        current_price = float(latest_price_cache[symbol])
        snapshot = valuation_cache.get(symbol, {})
        pe_ratio = snapshot.get("pe_ratio")
        try:
            bundle = load_trained_model_bundle(
                ticker=symbol,
                period="5y",
                target_name=target_name,
                model_name=model_name,
            )
        except ModelResultsError as exc:
            raise LiveVirtualTraderError(str(exc)) from exc
        model = bundle["model"]
        feature_names = list(bundle["feature_names"])
        task_type = str(bundle["task_type"]).lower()
        x_latest = pd.DataFrame([{name: latest_row.get(name, None) for name in feature_names}])

        prediction_value = float(model.predict(x_latest)[0])
        confidence_score = None
        if hasattr(model, "predict_proba"):
            try:
                probs = model.predict_proba(x_latest)
                confidence_score = float(max(probs[0]))
            except Exception:
                confidence_score = None

        explanation = build_prediction_explanation(
            feature_row=latest_row,
            task_type=task_type,
            predicted_value=prediction_value,
            confidence_score=confidence_score,
        )
        technical = explanation["technical_state_summary"]
        news = explanation["news_sentiment_summary"]
        benchmark_summary = explanation["benchmark_strength_summary"]

        position = holdings_by_ticker.get(symbol)
        bullish, bearish = _derive_signal_flags(prediction_value, task_type, min_predicted_return_pct)
        action = "no_action"
        reason = "model_not_bullish"
        quantity = 0.0
        volatility = float(latest_row.get("rolling_volatility_20_pct", 0.0) or 0.0)

        if position and float(position["quantity"]) > 0:
            entry = float(position["avg_entry_price"])
            quantity = float(position["quantity"])
            if stop_loss_pct > 0 and current_price <= entry * (1 - stop_loss_pct):
                action, reason = "sell", "stop_loss"
            elif take_profit_pct is not None and current_price >= entry * (1 + take_profit_pct):
                action, reason = "sell", "take_profit"
            elif bearish and _confidence_ok(confidence_score, confidence_threshold):
                action, reason = "sell", "model_bearish_signal"
            else:
                action, reason = "hold", "holding_position"
        else:
            if bullish and _confidence_ok(confidence_score, confidence_threshold):
                account = ledger.build_account_summary(clean_user_id, latest_prices=latest_price_cache)
                cash_available = float(account["cash"])
                equity = float(account["total_account_value"])
                holdings_count = len(account["holdings"])
                concentration_ok = holdings_count < 15
                valuation_ok = pe_ratio is None or float(pe_ratio) <= 85
                volatility_ok = volatility <= 55
                allocation = min(cash_available, float(equity * max_position_size_pct))
                if allocation > 0 and current_price > 0 and concentration_ok and valuation_ok and volatility_ok:
                    action, reason = "buy", "model_bullish_signal"
                    quantity = float(allocation / current_price)
                else:
                    action, reason = "no_action", "risk_or_cash_constraint"
            elif not _confidence_ok(confidence_score, confidence_threshold):
                action, reason = "no_action", "confidence_below_threshold"

        threshold_summary = (
            f"Thresholds: confidence {confidence_score:.0%} vs {confidence_threshold:.0%}; "
            f"max position {max_position_size_pct:.0%}; stop loss {stop_loss_pct:.0%}; "
            f"volatility20 {volatility:.1f}%; PE {pe_ratio if pe_ratio is not None else 'N/A'}."
            if confidence_score is not None
            else (
                f"Thresholds: confidence unavailable; required {confidence_threshold:.0%}; "
                f"max position {max_position_size_pct:.0%}; stop loss {stop_loss_pct:.0%}; "
                f"volatility20 {volatility:.1f}%; PE {pe_ratio if pe_ratio is not None else 'N/A'}."
            )
        )

        latest_trade_for_symbol = store.list_trades(clean_user_id, limit=1, ticker=symbol)
        if action in {"buy", "sell"} and latest_trade_for_symbol:
            previous = latest_trade_for_symbol[0]
            if (
                previous.get("action") == action
                and previous.get("reason") == reason
            ):
                action, reason = "no_action", "duplicate_signal_suppressed"
                quantity = 0.0

        now_ts = _utc_now()
        if action == "buy":
            try:
                ledger.create_trade_event(
                    user_id=clean_user_id,
                    action="buy",
                    ticker=symbol,
                    quantity=quantity,
                    price=current_price,
                    source="trader",
                    reason=reason,
                    metadata={
                        "model_name": model_name,
                        "confidence_score": confidence_score,
                        "prediction_value": prediction_value,
                    },
                )
            except AccountLedgerError as exc:
                action, reason = "no_action", f"ledger_rejected_buy:{exc}"
                quantity = 0.0
        elif action == "sell" and position:
            try:
                ledger.create_trade_event(
                    user_id=clean_user_id,
                    action="sell",
                    ticker=symbol,
                    quantity=quantity,
                    price=current_price,
                    source="trader",
                    reason=reason,
                    metadata={
                        "model_name": model_name,
                        "confidence_score": confidence_score,
                        "prediction_value": prediction_value,
                    },
                )
            except AccountLedgerError as exc:
                action, reason = "no_action", f"ledger_rejected_sell:{exc}"
                quantity = 0.0

        account = ledger.build_account_summary(
            clean_user_id,
            latest_prices=latest_price_cache,
        )
        updated_pos = {item["ticker"]: item for item in account["holdings"]}.get(symbol)
        holdings_after = float(updated_pos["quantity"]) if updated_pos else 0.0
        unrealized_after = float(updated_pos["unrealized_pnl"]) if updated_pos else 0.0
        action_summary = {
            "buy": "Simulated buy executed from latest model signal.",
            "sell": "Simulated sell executed from risk/model rule.",
            "hold": "Holding position. No exit trigger was hit.",
            "no_action": "No action taken. Entry conditions were not met.",
        }.get(action, "No action.")

        trade_payload = {
            "timestamp": now_ts,
            "user_id": clean_user_id,
            "ticker": symbol,
            "action": action,
            "quantity": float(quantity),
            "price": float(current_price),
            "model_name": model_name,
            "confidence_score": confidence_score,
            "reason": reason,
            "threshold_summary": threshold_summary,
            "technical_state_summary": technical,
            "news_sentiment_summary": news,
            "benchmark_strength_summary": benchmark_summary,
            "action_summary": action_summary,
            "cash_after": float(account["cash"]),
            "holdings_after": holdings_after,
            "realized_pnl": float(account["realized_pnl"]),
            "unrealized_pnl": unrealized_after,
            "metadata": {
                "prediction_value": prediction_value,
                "task_type": task_type,
                "price_date": str(latest_row.get("date")),
                "explanation": explanation["explanation"],
                "pe_ratio": pe_ratio,
                "volatility": volatility,
            },
        }
        store.append_trade(trade_payload)
        decisions.append(trade_payload)
        logger.info(
            "Live trader decision user_id=%s ticker=%s action=%s reason=%s prediction=%s confidence=%s",
            clean_user_id,
            symbol,
            action,
            reason,
            prediction_value,
            confidence_score,
        )

    account = ledger.build_account_summary(
        clean_user_id,
        latest_prices=latest_price_cache,
    )
    holdings = account["holdings"]
    holdings_value = float(account["holdings_value"])
    total_equity = float(account["total_account_value"])

    return LiveStatus(
        user_id=clean_user_id,
        model_name=model_name,
        generated_at_utc=_utc_now(),
        account={
            "cash": float(account["cash"]),
            "realized_pnl": float(account["realized_pnl"]),
            "total_contributions_applied": float(account["net_deposits"]),
            "holdings_value": holdings_value,
            "total_equity": total_equity,
        },
        holdings=holdings,
        latest_decisions=decisions,
        contribution_events=contribution_events,
    )


def get_live_virtual_trader_status(
    user_id: str,
    tickers: list[str] | None = None,
    model_name: str = "logistic_regression",
    auto_run: bool = False,
) -> LiveStatus:
    if auto_run:
        return run_live_virtual_trader_now(user_id=user_id, tickers=tickers, model_name=model_name)

    clean_user_id = str(user_id).strip()
    if not clean_user_id:
        raise LiveVirtualTraderError("user_id is required.")

    symbols = _resolve_user_tickers(clean_user_id, tickers)
    ledger = get_account_ledger_service()

    store = get_live_virtual_trader_store()
    latest_prices = _latest_prices_for_symbols(list(set(symbols)))
    account = ledger.build_account_summary(clean_user_id, latest_prices=latest_prices)
    holdings = account["holdings"]
    holdings_value = float(account["holdings_value"])
    total_equity = float(account["total_account_value"])
    trade_filter = symbols[0] if tickers and len(symbols) == 1 else None
    latest_decisions = store.list_trades(
        clean_user_id,
        limit=max(1, len(symbols)),
        ticker=trade_filter,
    )
    contribution_events = ledger.list_events(
        clean_user_id,
        limit=24,
        event_types=["monthly_contribution", "manual_deposit", "withdrawal"],
    )

    return LiveStatus(
        user_id=clean_user_id,
        model_name=model_name,
        generated_at_utc=_utc_now(),
        account={
            "cash": float(account["cash"]),
            "realized_pnl": float(account["realized_pnl"]),
            "total_contributions_applied": float(account["net_deposits"]),
            "holdings_value": holdings_value,
            "total_equity": total_equity,
        },
        holdings=holdings,
        latest_decisions=latest_decisions,
        contribution_events=contribution_events,
    )


def list_live_virtual_trader_trades(
    user_id: str,
    limit: int = 50,
    ticker: str | None = None,
) -> dict[str, Any]:
    clean_user_id = str(user_id).strip()
    if not clean_user_id:
        raise LiveVirtualTraderError("user_id is required.")
    store = get_live_virtual_trader_store()
    trades = store.list_trades(clean_user_id, limit=limit, ticker=ticker)
    return {
        "user_id": clean_user_id,
        "count": len(trades),
        "trades": trades,
        "contribution_application_history": get_account_ledger_service().list_events(
            clean_user_id,
            limit=100,
            event_types=["monthly_contribution", "manual_deposit", "withdrawal"],
        ),
    }


_STORE = LiveVirtualTraderStore()


def get_live_virtual_trader_store() -> LiveVirtualTraderStore:
    return _STORE
