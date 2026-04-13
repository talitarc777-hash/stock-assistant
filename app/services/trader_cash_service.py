"""Cash and contribution ledger for live virtual trader mode.

This service intentionally tracks only simulated account values.
No broker API calls and no real-money execution are performed.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.core.settings import get_settings
from app.services.monthly_contribution_service import START_MONTH

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _month_key(value: str) -> str:
    text = str(value).strip()
    if len(text) != 7 or text[4] != "-":
        raise ValueError("month must use YYYY-MM format.")
    year = int(text[:4])
    month = int(text[5:7])
    if month < 1 or month > 12:
        raise ValueError("month must use YYYY-MM format.")
    return f"{year:04d}-{month:02d}"


def _current_month_key() -> str:
    now = datetime.now(UTC)
    return f"{now.year:04d}-{now.month:02d}"


def _month_range(start_month: str, end_month: str) -> list[str]:
    start = _month_key(start_month)
    end = _month_key(end_month)
    start_year, start_m = int(start[:4]), int(start[5:7])
    end_year, end_m = int(end[:4]), int(end[5:7])
    values: list[str] = []
    year, month = start_year, start_m
    while (year, month) <= (end_year, end_m):
        values.append(f"{year:04d}-{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1
    return values


@dataclass(frozen=True)
class TraderAccountSnapshot:
    user_id: str
    cash: float
    realized_pnl: float
    total_contributions_applied: float
    updated_at: str


@dataclass(frozen=True)
class AppliedContributionEvent:
    user_id: str
    month: str
    configured_amount: float
    applied_amount: float
    delta_applied_now: float
    applied_at: str


class TraderCashService:
    """SQLite-backed cash ledger for live simulated trading."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = Path(db_path or get_settings().profile_db_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS live_trader_accounts (
                    user_id TEXT PRIMARY KEY,
                    cash REAL NOT NULL DEFAULT 0,
                    realized_pnl REAL NOT NULL DEFAULT 0,
                    total_contributions_applied REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS live_trader_monthly_contributions (
                    user_id TEXT NOT NULL,
                    month TEXT NOT NULL,
                    configured_amount REAL NOT NULL DEFAULT 0,
                    applied_amount REAL NOT NULL DEFAULT 0,
                    applied_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, month)
                )
                """
            )
            connection.commit()

    def _ensure_account(self, user_id: str) -> None:
        clean_user_id = str(user_id).strip()
        if not clean_user_id:
            raise ValueError("user_id is required.")
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO live_trader_accounts (
                    user_id, cash, realized_pnl, total_contributions_applied, created_at, updated_at
                ) VALUES (?, 0, 0, 0, ?, ?)
                ON CONFLICT(user_id) DO NOTHING
                """,
                (clean_user_id, now, now),
            )
            connection.commit()

    def get_account_snapshot(self, user_id: str) -> TraderAccountSnapshot:
        self._ensure_account(user_id)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM live_trader_accounts WHERE user_id = ?",
                (str(user_id).strip(),),
            ).fetchone()
        if row is None:
            raise ValueError("Live trader account was not found.")
        return TraderAccountSnapshot(
            user_id=row["user_id"],
            cash=float(row["cash"]),
            realized_pnl=float(row["realized_pnl"]),
            total_contributions_applied=float(row["total_contributions_applied"]),
            updated_at=row["updated_at"],
        )

    def apply_monthly_contributions(
        self,
        user_id: str,
        contribution_schedule: dict[str, float],
        current_month: str | None = None,
    ) -> list[AppliedContributionEvent]:
        """Apply monthly contribution deltas up to current month.

        This prevents duplicate counting by storing each month's applied amount.
        If a configured amount increases later (for the same month), only the delta
        is added to cash.
        """
        clean_user_id = str(user_id).strip()
        if not clean_user_id:
            raise ValueError("user_id is required.")
        self._ensure_account(clean_user_id)

        end_month = _month_key(current_month or _current_month_key())
        months = _month_range(START_MONTH, end_month)
        now = _utc_now()
        events: list[AppliedContributionEvent] = []

        with self._connect() as connection:
            total_delta = 0.0
            for month in months:
                configured = max(0.0, float(contribution_schedule.get(month, 0.0)))
                existing = connection.execute(
                    """
                    SELECT configured_amount, applied_amount, applied_at
                    FROM live_trader_monthly_contributions
                    WHERE user_id = ? AND month = ?
                    """,
                    (clean_user_id, month),
                ).fetchone()
                previously_applied = float(existing["applied_amount"]) if existing else 0.0
                delta = max(0.0, configured - previously_applied)
                new_applied = max(previously_applied, configured)
                applied_at = existing["applied_at"] if existing else now

                connection.execute(
                    """
                    INSERT INTO live_trader_monthly_contributions (
                        user_id, month, configured_amount, applied_amount, applied_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, month) DO UPDATE SET
                        configured_amount = excluded.configured_amount,
                        applied_amount = excluded.applied_amount,
                        updated_at = excluded.updated_at
                    """,
                    (clean_user_id, month, configured, new_applied, applied_at, now),
                )

                if delta > 0:
                    total_delta += delta
                    events.append(
                        AppliedContributionEvent(
                            user_id=clean_user_id,
                            month=month,
                            configured_amount=configured,
                            applied_amount=new_applied,
                            delta_applied_now=delta,
                            applied_at=now,
                        )
                    )

            if total_delta > 0:
                connection.execute(
                    """
                    UPDATE live_trader_accounts
                    SET cash = cash + ?,
                        total_contributions_applied = total_contributions_applied + ?,
                        updated_at = ?
                    WHERE user_id = ?
                    """,
                    (total_delta, total_delta, now, clean_user_id),
                )
                logger.info(
                    "Applied monthly contribution delta user_id=%s delta=%.2f months=%d",
                    clean_user_id,
                    total_delta,
                    len(events),
                )
            connection.commit()

        return events

    def adjust_cash_and_realized_pnl(
        self,
        user_id: str,
        cash_delta: float = 0.0,
        realized_pnl_delta: float = 0.0,
    ) -> TraderAccountSnapshot:
        self._ensure_account(user_id)
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE live_trader_accounts
                SET cash = cash + ?,
                    realized_pnl = realized_pnl + ?,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (float(cash_delta), float(realized_pnl_delta), now, str(user_id).strip()),
            )
            connection.commit()
        return self.get_account_snapshot(user_id)

    def list_applied_contribution_rows(self, user_id: str) -> list[dict[str, object]]:
        self._ensure_account(user_id)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT user_id, month, configured_amount, applied_amount, applied_at, updated_at
                FROM live_trader_monthly_contributions
                WHERE user_id = ?
                ORDER BY month ASC
                """,
                (str(user_id).strip(),),
            ).fetchall()
        return [
            {
                "user_id": row["user_id"],
                "month": row["month"],
                "configured_amount": float(row["configured_amount"]),
                "applied_amount": float(row["applied_amount"]),
                "applied_at": row["applied_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]


_SERVICE = TraderCashService()


def get_trader_cash_service() -> TraderCashService:
    return _SERVICE
