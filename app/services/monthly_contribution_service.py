"""SQLite-backed monthly contribution records for user-specific simulations."""

from __future__ import annotations

import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.core.settings import get_settings
from app.models.monthly_contribution import MonthlyContributionRecordResponse
from app.services.user_profile_service import get_user_profile_store

logger = logging.getLogger(__name__)

START_MONTH = "2026-04"


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


def _current_month_key() -> str:
    now = datetime.now(UTC)
    return f"{now.year:04d}-{now.month:02d}"


class MonthlyContributionStore:
    """Small data-access layer for user-specific monthly contribution records."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = Path(db_path or get_settings().profile_db_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS monthly_contributions (
                    user_id TEXT NOT NULL,
                    month TEXT NOT NULL,
                    amount REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, month)
                )
                """
            )
            connection.commit()

    def _row_to_record(self, row: sqlite3.Row) -> MonthlyContributionRecordResponse:
        return MonthlyContributionRecordResponse(
            user_id=row["user_id"],
            month=row["month"],
            amount=float(row["amount"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _fetch_records(self, user_id: str) -> list[MonthlyContributionRecordResponse]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM monthly_contributions
                WHERE user_id = ?
                ORDER BY month ASC
                """,
                (user_id,),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def initialize_for_user(self, user_id: str) -> list[MonthlyContributionRecordResponse]:
        """Ensure records exist from April 2026 through the current month."""
        clean_user_id = str(user_id).strip()
        if not clean_user_id:
            raise ValueError("user_id is required.")
        get_user_profile_store().get_or_create_profile(clean_user_id)

        all_months = _month_range(START_MONTH, _current_month_key())
        now = _utc_now()
        with self._connect() as connection:
            existing_rows = connection.execute(
                "SELECT month FROM monthly_contributions WHERE user_id = ?",
                (clean_user_id,),
            ).fetchall()
            existing_months = {row["month"] for row in existing_rows}
            missing_months = [month for month in all_months if month not in existing_months]
            for month in missing_months:
                connection.execute(
                    """
                    INSERT INTO monthly_contributions (user_id, month, amount, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (clean_user_id, month, 0.0, now, now),
                )
            connection.commit()

        if missing_months:
            logger.info(
                "Initialized monthly contributions user_id=%s months=%d start_month=%s",
                clean_user_id,
                len(missing_months),
                START_MONTH,
            )
        return self._fetch_records(clean_user_id)

    def list_records(self, user_id: str) -> list[MonthlyContributionRecordResponse]:
        """Return all contribution records in chronological order."""
        clean_user_id = str(user_id).strip()
        if not clean_user_id:
            raise ValueError("user_id is required.")
        self.initialize_for_user(clean_user_id)
        return self._fetch_records(clean_user_id)

    def update_amount(self, user_id: str, month: str, amount: float) -> MonthlyContributionRecordResponse:
        """Update one month's available money."""
        clean_user_id = str(user_id).strip()
        if not clean_user_id:
            raise ValueError("user_id is required.")
        clean_month = _month_key(month)
        if clean_month < START_MONTH:
            raise ValueError(f"month must be {START_MONTH} or later.")
        try:
            numeric_amount = float(amount)
        except (TypeError, ValueError) as exc:
            raise ValueError("amount must be numeric.") from exc
        if numeric_amount < 0:
            raise ValueError("amount must be non-negative.")

        self.initialize_for_user(clean_user_id)
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE monthly_contributions
                SET amount = ?, updated_at = ?
                WHERE user_id = ? AND month = ?
                """,
                (numeric_amount, now, clean_user_id, clean_month),
            )
            connection.commit()
            row = connection.execute(
                """
                SELECT * FROM monthly_contributions
                WHERE user_id = ? AND month = ?
                """,
                (clean_user_id, clean_month),
            ).fetchone()
        if row is None:
            raise ValueError("Failed to update monthly contribution record.")
        logger.info(
            "Updated monthly contribution user_id=%s month=%s amount=%.2f",
            clean_user_id,
            clean_month,
            numeric_amount,
        )
        return self._row_to_record(row)

    def get_amount_map(self, user_id: str) -> dict[str, float]:
        """Return a month-to-amount mapping for simulation use."""
        return {record.month: record.amount for record in self.list_records(user_id)}


_STORE = MonthlyContributionStore()


def get_monthly_contribution_store() -> MonthlyContributionStore:
    """Return the shared monthly contribution store singleton."""
    return _STORE
