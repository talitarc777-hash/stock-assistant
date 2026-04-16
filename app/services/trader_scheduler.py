"""Background scheduler for continuous live virtual trader simulation.

This keeps infrastructure intentionally simple:
- one in-process background thread
- one in-memory lock to prevent overlapping runs
- cadence changes by U.S. market-hours mode
"""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime, timedelta
import logging
from threading import Event, Lock, Thread
from typing import Any

from app.services.account_ledger_service import get_account_ledger_service
from app.services.live_virtual_trader import LiveStatus, run_live_virtual_trader_now
from app.services.market_hours_service import get_market_hours_state
from app.services.model_selection_service import resolve_selected_model_name
from app.services.user_profile_service import get_user_profile_store

logger = logging.getLogger(__name__)


class TraderSchedulerBusyError(Exception):
    """Raised when a scheduler/manual run is requested while another run is active."""


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


class TraderSchedulerService:
    """In-process trader scheduler with market-aware cadence and run locking."""

    def __init__(self) -> None:
        self._stop_event = Event()
        self._run_lock = Lock()
        self._state_lock = Lock()
        self._thread: Thread | None = None

        self._running = False
        self._scheduler_started = False
        self._mode = "market_closed"
        self._cadence_seconds = 3600
        self._last_run_time_utc: str | None = None
        self._next_run_time_utc: str | None = None
        self._total_runs = 0
        self._skipped_runs_total = 0
        self._last_decisions_total = 0
        self._last_decisions_executed = 0
        self._last_error_count = 0
        self._consecutive_failures = 0
        self._recent_runs: deque[dict[str, Any]] = deque(maxlen=200)

    def start(self) -> None:
        """Start the background scheduler thread once."""
        with self._state_lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            state = get_market_hours_state()
            self._mode = state.mode
            self._cadence_seconds = state.interval_seconds
            self._next_run_time_utc = (
                datetime.now(UTC) + timedelta(seconds=self._cadence_seconds)
            ).replace(microsecond=0).isoformat()
            self._thread = Thread(
                target=self._run_loop,
                name="stock-assistant-trader-scheduler",
                daemon=True,
            )
            self._thread.start()
            self._scheduler_started = True
        logger.info(
            "Trader scheduler started mode=%s cadence_seconds=%d",
            self._mode,
            self._cadence_seconds,
        )

    def stop(self, timeout_seconds: float = 5.0) -> None:
        """Stop the background scheduler thread gracefully."""
        self._stop_event.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=timeout_seconds)
        with self._state_lock:
            self._running = False
            self._scheduler_started = False
            self._thread = None
            self._next_run_time_utc = None
        logger.info("Trader scheduler stopped")

    def _target_users_for_scheduler(self) -> list[str]:
        rows = get_user_profile_store().list_alert_enabled_user_summaries()
        users = [row.user_id for row in rows if str(row.user_id).strip()]
        if not users:
            users = ["demo-user"]
        return users

    def _append_run_log(
        self,
        *,
        source: str,
        mode: str,
        users_scanned: int,
        decisions_total: int,
        decisions_executed: int,
        skipped: bool,
        message: str,
        error_count: int = 0,
        error_messages: list[str] | None = None,
    ) -> None:
        row = {
            "timestamp_utc": _utc_now_iso(),
            "source": source,
            "mode": mode,
            "users_scanned": int(users_scanned),
            "decisions_total": int(decisions_total),
            "decisions_executed": int(decisions_executed),
            "skipped": bool(skipped),
            "message": message,
            "error_count": int(error_count),
            "error_messages": list(error_messages or []),
        }
        with self._state_lock:
            self._recent_runs.appendleft(row)
            if skipped:
                self._skipped_runs_total += 1
            else:
                self._total_runs += 1
                self._last_run_time_utc = row["timestamp_utc"]
                self._last_decisions_total = int(decisions_total)
                self._last_decisions_executed = int(decisions_executed)
                self._last_error_count = int(error_count)
                if int(error_count) > 0:
                    self._consecutive_failures += 1
                else:
                    self._consecutive_failures = 0
        logger.info(
            "Trader run source=%s mode=%s users=%d decisions_executed=%d decisions_total=%d errors=%d skipped=%s",
            source,
            mode,
            users_scanned,
            decisions_executed,
            decisions_total,
            error_count,
            skipped,
        )

    def _record_skip(self, source: str, reason: str) -> None:
        state = get_market_hours_state()
        self._append_run_log(
            source=source,
            mode=state.mode,
            users_scanned=0,
            decisions_total=0,
            decisions_executed=0,
            skipped=True,
            message=reason,
            error_count=0,
            error_messages=[],
        )
        logger.info("Trader run skipped source=%s reason=%s", source, reason)

    @staticmethod
    def _count_executed_decisions(decisions: list[dict[str, Any]]) -> int:
        return sum(
            1 for row in decisions if str(row.get("action", "")).lower() in {"buy", "sell", "hold"}
        )

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            self.run_cycle(source="scheduler", raise_if_busy=False)
            state = get_market_hours_state()
            with self._state_lock:
                self._mode = state.mode
                self._cadence_seconds = state.interval_seconds
                self._next_run_time_utc = (
                    datetime.now(UTC) + timedelta(seconds=self._cadence_seconds)
                ).replace(microsecond=0).isoformat()
                cadence_seconds = self._cadence_seconds
            if self._stop_event.wait(cadence_seconds):
                break

    @staticmethod
    def _run_live_trader_with_retry(
        *,
        user_id: str,
        model_name: str,
        tickers: list[str] | None = None,
        max_attempts: int = 2,
    ) -> LiveStatus:
        """Run live trader with a tiny retry budget for transient data-fetch failures."""
        last_error: Exception | None = None
        attempts = max(1, int(max_attempts))
        for attempt in range(1, attempts + 1):
            try:
                return run_live_virtual_trader_now(
                    user_id=user_id,
                    tickers=tickers,
                    model_name=model_name,
                )
            except Exception as exc:  # pragma: no cover - runtime defensive guard
                last_error = exc
                logger.warning(
                    "Trader attempt failed user_id=%s attempt=%d/%d error=%s",
                    user_id,
                    attempt,
                    attempts,
                    exc,
                )
        assert last_error is not None
        raise last_error

    def run_cycle(
        self,
        *,
        source: str = "scheduler",
        user_ids: list[str] | None = None,
        raise_if_busy: bool = True,
    ) -> None:
        """Execute one scheduler cycle for one or multiple users."""
        acquired = self._run_lock.acquire(blocking=False)
        if not acquired:
            self._record_skip(source, "previous_run_still_executing")
            if raise_if_busy:
                raise TraderSchedulerBusyError("Trader is already running. Try again shortly.")
            return

        state = get_market_hours_state()
        with self._state_lock:
            self._running = True
            self._mode = state.mode
            self._cadence_seconds = state.interval_seconds

        users = user_ids or self._target_users_for_scheduler()
        decisions_total = 0
        decisions_executed = 0
        error_count = 0
        error_messages: list[str] = []
        ledger = get_account_ledger_service()

        try:
            for user_id in users:
                clean_user_id = str(user_id).strip()
                if not clean_user_id:
                    continue
                try:
                    ledger.apply_recurring_monthly_contribution_if_due(
                        clean_user_id,
                        source="scheduler",
                    )
                    selected_model_name = resolve_selected_model_name(user_id=clean_user_id)
                    status = self._run_live_trader_with_retry(
                        user_id=clean_user_id,
                        model_name=selected_model_name,
                        max_attempts=2,
                    )
                    user_decisions = list(status.latest_decisions)
                    decisions_total += len(user_decisions)
                    decisions_executed += self._count_executed_decisions(user_decisions)
                except Exception as exc:  # pragma: no cover - runtime defensive guard
                    error_count += 1
                    error_messages.append(f"{clean_user_id}: {str(exc)}")
                    logger.exception("Trader cycle failed user_id=%s error=%s", clean_user_id, exc)

            message = (
                f"run_completed users={len(users)} errors={error_count}"
                if users
                else "run_completed no_users"
            )
            self._append_run_log(
                source=source,
                mode=state.mode,
                users_scanned=len(users),
                decisions_total=decisions_total,
                decisions_executed=decisions_executed,
                skipped=False,
                message=message,
                error_count=error_count,
                error_messages=error_messages,
            )
        finally:
            with self._state_lock:
                self._running = False
            self._run_lock.release()

    def run_user_now(
        self,
        *,
        user_id: str,
        tickers: list[str] | None = None,
        model_name: str | None = None,
    ) -> LiveStatus:
        """Run one immediate manual cycle using the same lock as scheduler runs."""
        clean_user_id = str(user_id).strip()
        if not clean_user_id:
            raise ValueError("user_id is required.")

        acquired = self._run_lock.acquire(blocking=False)
        if not acquired:
            self._record_skip("manual", "previous_run_still_executing")
            raise TraderSchedulerBusyError("Trader is already running. Try again shortly.")

        state = get_market_hours_state()
        with self._state_lock:
            self._running = True
            self._mode = state.mode
            self._cadence_seconds = state.interval_seconds

        try:
            get_account_ledger_service().apply_recurring_monthly_contribution_if_due(
                clean_user_id,
                source="scheduler",
            )
            selected_model_name = resolve_selected_model_name(
                user_id=clean_user_id,
                requested_model_name=model_name,
            )
            status = self._run_live_trader_with_retry(
                user_id=clean_user_id,
                model_name=selected_model_name,
                tickers=tickers,
                max_attempts=2,
            )
            decisions_total = len(status.latest_decisions)
            decisions_executed = self._count_executed_decisions(status.latest_decisions)
            self._append_run_log(
                source="manual",
                mode=state.mode,
                users_scanned=1,
                decisions_total=decisions_total,
                decisions_executed=decisions_executed,
                skipped=False,
                message=f"manual_run_completed user_id={clean_user_id}",
                error_count=0,
                error_messages=[],
            )
            return status
        finally:
            with self._state_lock:
                self._running = False
            self._run_lock.release()

    def get_status(self, log_limit: int = 8) -> dict[str, Any]:
        """Return scheduler status snapshot for web/Discord surfaces."""
        state = get_market_hours_state()
        with self._state_lock:
            mode = self._mode or state.mode
            cadence_seconds = int(self._cadence_seconds or state.interval_seconds)
            next_run = self._next_run_time_utc
            if not next_run and self._scheduler_started:
                next_run = (
                    datetime.now(UTC) + timedelta(seconds=cadence_seconds)
                ).replace(microsecond=0).isoformat()

            recent_runs = list(self._recent_runs)[: max(1, int(log_limit))]
            return {
                "running": bool(self._running),
                "scheduler_started": bool(self._scheduler_started),
                "mode": mode,
                "cadence_seconds": cadence_seconds,
                "cadence_label": (
                    "5 minutes" if mode == "market_open" else "1 hour"
                ),
                "last_run_time_utc": self._last_run_time_utc,
                "next_run_time_utc": next_run,
                "total_runs": int(self._total_runs),
                "skipped_runs_total": int(self._skipped_runs_total),
                "last_decisions_total": int(self._last_decisions_total),
                "last_decisions_executed": int(self._last_decisions_executed),
                "last_error_count": int(self._last_error_count),
                "recent_runs": recent_runs,
            }

    def get_health(self) -> dict[str, Any]:
        """Return a minimal scheduler health snapshot."""
        status = self.get_status(log_limit=1)
        healthy = bool(status["scheduler_started"]) and (
            int(self._consecutive_failures) < 5
        )
        return {
            "healthy": healthy,
            "scheduler_started": bool(status["scheduler_started"]),
            "running": bool(status["running"]),
            "mode": str(status["mode"]),
            "last_run_time_utc": status["last_run_time_utc"],
            "next_run_time_utc": status["next_run_time_utc"],
            "consecutive_failures": int(self._consecutive_failures),
        }


_SERVICE = TraderSchedulerService()


def get_trader_scheduler_service() -> TraderSchedulerService:
    """Return the shared trader scheduler singleton."""
    return _SERVICE
