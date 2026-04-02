"""SQLite persistence for scenario-based forecast snapshots.

This module keeps a simple local history so we can evaluate forecast quality later.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


class ForecastStoreError(Exception):
    """Raised when forecast snapshot storage fails."""


@dataclass(frozen=True)
class ForecastSnapshot:
    """One stored forecast snapshot row."""

    timestamp_utc: str
    ticker: str
    close: float
    trend_regime: str
    outlook_5d: str
    outlook_20d: str
    expected_range_lower: float
    expected_range_upper: float
    confidence_score: int


def _db_path() -> Path:
    """Return the local SQLite database path."""
    return Path("data") / "forecast_snapshots.db"


def _connect() -> sqlite3.Connection:
    """Open SQLite connection and ensure parent directory exists."""
    db_path = _db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def _ensure_table(connection: sqlite3.Connection) -> None:
    """Create storage table if it does not exist yet."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS forecast_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT NOT NULL,
            ticker TEXT NOT NULL,
            close REAL NOT NULL,
            trend_regime TEXT NOT NULL,
            outlook_5d TEXT NOT NULL,
            outlook_20d TEXT NOT NULL,
            expected_range_lower REAL NOT NULL,
            expected_range_upper REAL NOT NULL,
            confidence_score INTEGER NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_forecast_ticker_time "
        "ON forecast_snapshots (ticker, timestamp_utc DESC)"
    )


def save_forecast_snapshot(
    ticker: str,
    close: float,
    trend_regime: str,
    outlook_5d: str,
    outlook_20d: str,
    expected_range_lower: float,
    expected_range_upper: float,
    confidence_score: int,
) -> None:
    """Save one forecast run snapshot."""
    timestamp_utc = datetime.now(timezone.utc).isoformat()
    safe_ticker = ticker.strip().upper()

    try:
        with _connect() as connection:
            _ensure_table(connection)
            connection.execute(
                """
                INSERT INTO forecast_snapshots (
                    timestamp_utc,
                    ticker,
                    close,
                    trend_regime,
                    outlook_5d,
                    outlook_20d,
                    expected_range_lower,
                    expected_range_upper,
                    confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp_utc,
                    safe_ticker,
                    float(close),
                    trend_regime,
                    outlook_5d,
                    outlook_20d,
                    float(expected_range_lower),
                    float(expected_range_upper),
                    int(confidence_score),
                ),
            )
    except sqlite3.Error as exc:
        raise ForecastStoreError(f"Failed to save forecast snapshot for '{safe_ticker}'.") from exc


def get_forecast_history(ticker: str, limit: int = 200) -> list[ForecastSnapshot]:
    """Load recent forecast snapshots for one ticker."""
    safe_ticker = ticker.strip().upper()
    safe_limit = max(1, min(int(limit), 1000))

    try:
        with _connect() as connection:
            _ensure_table(connection)
            rows = connection.execute(
                """
                SELECT
                    timestamp_utc,
                    ticker,
                    close,
                    trend_regime,
                    outlook_5d,
                    outlook_20d,
                    expected_range_lower,
                    expected_range_upper,
                    confidence_score
                FROM forecast_snapshots
                WHERE ticker = ?
                ORDER BY timestamp_utc DESC
                LIMIT ?
                """,
                (safe_ticker, safe_limit),
            ).fetchall()
    except sqlite3.Error as exc:
        raise ForecastStoreError(f"Failed to load forecast history for '{safe_ticker}'.") from exc

    return [
        ForecastSnapshot(
            timestamp_utc=row[0],
            ticker=row[1],
            close=float(row[2]),
            trend_regime=row[3],
            outlook_5d=row[4],
            outlook_20d=row[5],
            expected_range_lower=float(row[6]),
            expected_range_upper=float(row[7]),
            confidence_score=int(row[8]),
        )
        for row in rows
    ]

