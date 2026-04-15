"""Immutable virtual account ledger and derived-account helpers.

This service is intentionally append-only:
- historical events are never updated in place
- account cash/holdings are rebuilt from ledger records
- corrections should be done as compensating events
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.settings import get_settings
from app.models.account_ledger import LEDGER_EVENT_TYPES
from app.services.market_data import get_price_history
from app.services.monthly_contribution_service import START_MONTH

logger = logging.getLogger(__name__)


class AccountLedgerError(Exception):
    """Raised when immutable ledger operations fail validation."""


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _clean_user_id(user_id: str) -> str:
    value = str(user_id).strip()
    if not value:
        raise AccountLedgerError("user_id is required.")
    return value


def _clean_month(month: str) -> str:
    value = str(month).strip()
    if len(value) != 7 or value[4] != "-":
        raise AccountLedgerError("month must use YYYY-MM format.")
    year = int(value[:4])
    m = int(value[5:7])
    if m < 1 or m > 12:
        raise AccountLedgerError("month must use YYYY-MM format.")
    normalized = f"{year:04d}-{m:02d}"
    if normalized < START_MONTH:
        raise AccountLedgerError(f"month must be {START_MONTH} or later.")
    return normalized


def _month_range(start_month: str, end_month: str) -> list[str]:
    start = _clean_month(start_month)
    end = _clean_month(end_month)
    sy, sm = int(start[:4]), int(start[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    values: list[str] = []
    year, month = sy, sm
    while (year, month) <= (ey, em):
        values.append(f"{year:04d}-{month:02d}")
        month += 1
        if month > 12:
            year += 1
            month = 1
    return values


def _current_month() -> str:
    now = datetime.now(UTC)
    return f"{now.year:04d}-{now.month:02d}"


@dataclass
class _HoldingState:
    ticker: str
    quantity: float
    avg_entry_price: float
    realized_pnl: float = 0.0


class AccountLedgerService:
    """SQLite-backed append-only ledger for virtual account simulation."""

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
                CREATE TABLE IF NOT EXISTS account_ledger_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    ticker TEXT,
                    quantity REAL,
                    price REAL,
                    reason TEXT,
                    source TEXT,
                    reference_month TEXT,
                    created_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_ledger_unique_monthly
                ON account_ledger_events(user_id, event_type, reference_month)
                WHERE event_type = 'monthly_contribution'
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ledger_user_created
                ON account_ledger_events(user_id, created_at, id)
                """
            )
            conn.commit()

    def _insert_event(
        self,
        *,
        user_id: str,
        event_type: str,
        amount: float,
        ticker: str | None = None,
        quantity: float | None = None,
        price: float | None = None,
        reason: str | None = None,
        source: str | None = None,
        reference_month: str | None = None,
        metadata: dict[str, Any] | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        clean_user_id = _clean_user_id(user_id)
        normalized_type = str(event_type).strip().lower()
        if normalized_type not in LEDGER_EVENT_TYPES:
            raise AccountLedgerError(f"Unsupported event_type: {event_type}.")
        if not isinstance(amount, (int, float)):
            raise AccountLedgerError("amount must be numeric.")

        payload_created_at = created_at or _utc_now()
        payload_metadata = metadata or {}
        payload_month = _clean_month(reference_month) if reference_month else None
        normalized_ticker = str(ticker).strip().upper() if ticker else None

        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO account_ledger_events (
                        user_id, event_type, amount, ticker, quantity, price, reason,
                        source, reference_month, created_at, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        clean_user_id,
                        normalized_type,
                        float(amount),
                        normalized_ticker,
                        float(quantity) if quantity is not None else None,
                        float(price) if price is not None else None,
                        (reason or "").strip() or None,
                        (source or "").strip() or None,
                        payload_month,
                        payload_created_at,
                        json.dumps(payload_metadata, ensure_ascii=False),
                    ),
                )
                event_id = int(cursor.lastrowid)
                conn.commit()
        except sqlite3.IntegrityError as exc:
            if normalized_type == "monthly_contribution":
                raise AccountLedgerError(
                    "This monthly contribution already exists and is immutable."
                ) from exc
            raise AccountLedgerError("Failed to persist ledger event.") from exc

        logger.info(
            "Ledger event created user_id=%s type=%s amount=%.2f ticker=%s month=%s source=%s",
            clean_user_id,
            normalized_type,
            float(amount),
            normalized_ticker or "",
            payload_month or "",
            source or "",
        )
        return self.get_event_by_id(event_id)

    def get_event_by_id(self, event_id: int) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM account_ledger_events WHERE id = ?",
                (int(event_id),),
            ).fetchone()
        if row is None:
            raise AccountLedgerError("Ledger event was not found.")
        return self._row_to_dict(row)

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        try:
            metadata = json.loads(row["metadata_json"] or "{}")
        except json.JSONDecodeError:
            metadata = {}
        return {
            "id": int(row["id"]),
            "user_id": row["user_id"],
            "event_type": row["event_type"],
            "amount": float(row["amount"]),
            "ticker": row["ticker"],
            "quantity": float(row["quantity"]) if row["quantity"] is not None else None,
            "price": float(row["price"]) if row["price"] is not None else None,
            "reason": row["reason"],
            "source": row["source"],
            "reference_month": row["reference_month"],
            "created_at": row["created_at"],
            "metadata": metadata,
        }

    def list_events(
        self,
        user_id: str,
        limit: int = 200,
        event_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        clean_user_id = _clean_user_id(user_id)
        sql = "SELECT * FROM account_ledger_events WHERE user_id = ?"
        params: list[Any] = [clean_user_id]
        if event_types:
            normalized = [item.strip().lower() for item in event_types if item.strip()]
            if normalized:
                placeholders = ",".join("?" for _ in normalized)
                sql += f" AND event_type IN ({placeholders})"
                params.extend(normalized)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(max(1, int(limit)))
        with self._connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def create_monthly_contribution(
        self,
        user_id: str,
        month: str,
        amount: float,
        source: str = "web",
        reason: str | None = None,
    ) -> dict[str, Any]:
        normalized_month = _clean_month(month)
        numeric_amount = float(amount)
        if numeric_amount <= 0:
            raise AccountLedgerError("amount must be greater than 0.")
        return self._insert_event(
            user_id=user_id,
            event_type="monthly_contribution",
            amount=numeric_amount,
            reason=reason or "monthly contribution",
            source=source,
            reference_month=normalized_month,
            metadata={"month": normalized_month},
        )

    def create_manual_deposit(
        self,
        user_id: str,
        amount: float,
        source: str = "web",
        reason: str | None = None,
    ) -> dict[str, Any]:
        numeric_amount = float(amount)
        if numeric_amount <= 0:
            raise AccountLedgerError("amount must be greater than 0.")
        return self._insert_event(
            user_id=user_id,
            event_type="manual_deposit",
            amount=numeric_amount,
            reason=reason or "manual deposit",
            source=source,
        )

    def create_withdrawal(
        self,
        user_id: str,
        amount: float,
        source: str = "web",
        reason: str | None = None,
    ) -> dict[str, Any]:
        numeric_amount = float(amount)
        if numeric_amount <= 0:
            raise AccountLedgerError("amount must be greater than 0.")

        summary = self.build_account_summary(user_id=user_id)
        if summary["cash"] < numeric_amount:
            raise AccountLedgerError("Insufficient cash for withdrawal.")
        return self._insert_event(
            user_id=user_id,
            event_type="withdrawal",
            amount=-numeric_amount,
            reason=reason or "withdrawal",
            source=source,
        )

    def create_trade_event(
        self,
        *,
        user_id: str,
        action: str,
        ticker: str,
        quantity: float,
        price: float,
        source: str = "trader",
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_action = str(action).strip().lower()
        if normalized_action not in {"buy", "sell"}:
            raise AccountLedgerError("trade action must be buy or sell.")
        numeric_quantity = float(quantity)
        numeric_price = float(price)
        if numeric_quantity <= 0 or numeric_price <= 0:
            raise AccountLedgerError("quantity and price must be greater than 0.")

        amount = -numeric_quantity * numeric_price if normalized_action == "buy" else numeric_quantity * numeric_price
        event_type = "buy_trade" if normalized_action == "buy" else "sell_trade"
        return self._insert_event(
            user_id=user_id,
            event_type=event_type,
            amount=amount,
            ticker=ticker,
            quantity=numeric_quantity,
            price=numeric_price,
            reason=reason or f"{normalized_action} trade",
            source=source,
            metadata=metadata or {},
        )

    def list_monthly_contribution_records(self, user_id: str) -> list[dict[str, Any]]:
        clean_user_id = _clean_user_id(user_id)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT reference_month, amount, created_at, id
                FROM account_ledger_events
                WHERE user_id = ? AND event_type = 'monthly_contribution'
                ORDER BY reference_month ASC, id ASC
                """,
                (clean_user_id,),
            ).fetchall()
        seen: set[str] = set()
        records: list[dict[str, Any]] = []
        for row in rows:
            month = row["reference_month"]
            if not month or month in seen:
                continue
            seen.add(month)
            records.append(
                {
                    "month": month,
                    "amount": float(row["amount"]),
                    "created_at": row["created_at"],
                    "locked": True,
                }
            )
        return records

    def build_monthly_contribution_view(self, user_id: str) -> list[dict[str, Any]]:
        clean_user_id = _clean_user_id(user_id)
        existing = {row["month"]: row for row in self.list_monthly_contribution_records(clean_user_id)}
        rows: list[dict[str, Any]] = []
        for month in _month_range(START_MONTH, _current_month()):
            if month in existing:
                row = existing[month]
                rows.append(
                    {
                        "user_id": clean_user_id,
                        "month": month,
                        "amount": row["amount"],
                        "created_at": row["created_at"],
                        "updated_at": row["created_at"],
                        "locked": True,
                    }
                )
            else:
                rows.append(
                    {
                        "user_id": clean_user_id,
                        "month": month,
                        "amount": 0.0,
                        "created_at": "",
                        "updated_at": "",
                        "locked": False,
                    }
                )
        return rows

    def _rebuild_holdings(self, user_id: str) -> tuple[dict[str, _HoldingState], float]:
        clean_user_id = _clean_user_id(user_id)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM account_ledger_events
                WHERE user_id = ? AND event_type IN ('buy_trade', 'sell_trade')
                ORDER BY id ASC
                """,
                (clean_user_id,),
            ).fetchall()

        holdings: dict[str, _HoldingState] = {}
        realized_total = 0.0
        for row in rows:
            ticker = (row["ticker"] or "").upper()
            if not ticker:
                continue
            qty = float(row["quantity"] or 0.0)
            price = float(row["price"] or 0.0)
            if qty <= 0 or price <= 0:
                continue
            state = holdings.get(ticker) or _HoldingState(ticker=ticker, quantity=0.0, avg_entry_price=0.0)
            if row["event_type"] == "buy_trade":
                new_qty = state.quantity + qty
                new_avg = ((state.quantity * state.avg_entry_price) + (qty * price)) / new_qty if new_qty > 0 else 0.0
                state.quantity = new_qty
                state.avg_entry_price = new_avg
            else:
                sell_qty = min(qty, state.quantity)
                if sell_qty <= 0:
                    continue
                realized = (price - state.avg_entry_price) * sell_qty
                realized_total += realized
                state.quantity -= sell_qty
                if state.quantity <= 1e-8:
                    state.quantity = 0.0
                    state.avg_entry_price = 0.0
            holdings[ticker] = state
        holdings = {key: value for key, value in holdings.items() if value.quantity > 0}
        return holdings, realized_total

    def build_account_summary(
        self,
        user_id: str,
        latest_prices: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        clean_user_id = _clean_user_id(user_id)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0) AS cash
                FROM account_ledger_events
                WHERE user_id = ?
                """,
                (clean_user_id,),
            ).fetchone()
            cash_value = float(row["cash"] if row is not None else 0.0)

            net_row = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0) AS net_deposits
                FROM account_ledger_events
                WHERE user_id = ?
                  AND event_type IN ('monthly_contribution', 'manual_deposit', 'withdrawal')
                """,
                (clean_user_id,),
            ).fetchone()
            net_deposits = float(net_row["net_deposits"] if net_row is not None else 0.0)

        holdings_map, realized_pnl = self._rebuild_holdings(clean_user_id)
        price_map = dict(latest_prices or {})
        if holdings_map:
            missing = [ticker for ticker in holdings_map if ticker not in price_map]
            for ticker in missing:
                df = get_price_history(ticker, period="3mo")
                price_map[ticker] = float(df.sort_values("date").iloc[-1]["close"])

        holdings_rows: list[dict[str, Any]] = []
        holdings_value = 0.0
        unrealized_total = 0.0
        for ticker, state in sorted(holdings_map.items()):
            market_price = float(price_map.get(ticker, 0.0))
            market_value = state.quantity * market_price
            unrealized = (market_price - state.avg_entry_price) * state.quantity
            holdings_value += market_value
            unrealized_total += unrealized
            holdings_rows.append(
                {
                    "ticker": ticker,
                    "quantity": state.quantity,
                    "avg_entry_price": state.avg_entry_price,
                    "current_price": market_price,
                    "market_value": market_value,
                    "unrealized_pnl": unrealized,
                }
            )

        return {
            "user_id": clean_user_id,
            "as_of": _utc_now(),
            "cash": cash_value,
            "holdings_value": holdings_value,
            "total_account_value": cash_value + holdings_value,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_total,
            "net_deposits": net_deposits,
            "holdings": holdings_rows,
            "latest_prices": price_map,
        }


_SERVICE = AccountLedgerService()


def get_account_ledger_service() -> AccountLedgerService:
    return _SERVICE
