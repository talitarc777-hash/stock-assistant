"""Typed models for trader scheduler status endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class TraderSchedulerRunLogResponse(BaseModel):
    """One recent scheduler/manual run record."""

    timestamp_utc: str
    source: str
    mode: str
    users_scanned: int
    decisions_total: int
    decisions_executed: int
    skipped: bool
    message: str


class TraderSchedulerStatusResponse(BaseModel):
    """Current scheduler runtime status snapshot."""

    running: bool
    scheduler_started: bool
    mode: str
    cadence_seconds: int
    cadence_label: str
    last_run_time_utc: str | None = None
    next_run_time_utc: str | None = None
    total_runs: int
    skipped_runs_total: int
    last_decisions_total: int
    last_decisions_executed: int
    recent_runs: list[TraderSchedulerRunLogResponse]
