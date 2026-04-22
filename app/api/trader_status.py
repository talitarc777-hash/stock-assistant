"""Scheduler status endpoints for continuous live virtual trader runs."""

from __future__ import annotations

import logging
from time import perf_counter

from fastapi import APIRouter, HTTPException, Query

from app.core.ttl_cache import TTLCache
from app.models.trader_scheduler import TraderSchedulerStatusResponse
from app.models.trader_scheduler import TraderSchedulerHealthResponse
from app.services.trader_scheduler import (
    TraderSchedulerBusyError,
    get_trader_scheduler_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["virtual-trader-scheduler"])
_STATUS_CACHE: TTLCache[dict] = TTLCache(max_items=16)


def _status_cache_key(recent_hours: int) -> str:
    return f"scheduler-status:{int(recent_hours)}"


@router.get("/virtual-trader/scheduler-status", response_model=TraderSchedulerStatusResponse)
def get_virtual_trader_scheduler_status(
    recent_hours: int = Query(24, ge=1, le=72),
) -> TraderSchedulerStatusResponse:
    """Return scheduler mode, cadence, run state, and recent run logs."""
    started = perf_counter()
    try:
        key = _status_cache_key(recent_hours)
        status = _STATUS_CACHE.get(key)
        if status is None:
            status = get_trader_scheduler_service().get_status(recent_hours=recent_hours)
            _STATUS_CACHE.set(key, status, ttl_seconds=5.0)
        elapsed_ms = (perf_counter() - started) * 1000.0
        logger.info(
            "trader-status fetched recent_hours=%d runs=%d elapsed_ms=%.1f",
            int(recent_hours),
            len(status.get("recent_runs", [])),
            elapsed_ms,
        )
        return TraderSchedulerStatusResponse(**status)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected scheduler status error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.get("/trader-status", response_model=TraderSchedulerStatusResponse)
def get_virtual_trader_scheduler_status_alias(
    recent_hours: int = Query(24, ge=1, le=72),
) -> TraderSchedulerStatusResponse:
    """Alias endpoint kept for simpler external integrations."""
    return get_virtual_trader_scheduler_status(recent_hours=recent_hours)


@router.get("/virtual-trader/scheduler-health", response_model=TraderSchedulerHealthResponse)
def get_virtual_trader_scheduler_health() -> TraderSchedulerHealthResponse:
    """Simple health endpoint for scheduler monitoring."""
    try:
        health = get_trader_scheduler_service().get_health()
        return TraderSchedulerHealthResponse(**health)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected scheduler health error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.post("/virtual-trader/scheduler-run-now", response_model=TraderSchedulerStatusResponse)
def run_virtual_trader_scheduler_now(
    user_id: str | None = Query(default=None, min_length=1, max_length=120),
    recent_hours: int = Query(24, ge=1, le=72),
) -> TraderSchedulerStatusResponse:
    """Trigger one immediate scheduler cycle (all users or one user)."""
    scheduler = get_trader_scheduler_service()
    try:
        if user_id:
            scheduler.run_cycle(
                source="manual_scheduler",
                user_ids=[user_id],
                raise_if_busy=True,
            )
        else:
            scheduler.run_cycle(source="manual_scheduler", raise_if_busy=True)
        _STATUS_CACHE.invalidate_prefix("scheduler-status:")
        status = scheduler.get_status(recent_hours=recent_hours)
        return TraderSchedulerStatusResponse(**status)
    except TraderSchedulerBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected scheduler run-now error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc
