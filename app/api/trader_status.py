"""Scheduler status endpoints for continuous live virtual trader runs."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.models.trader_scheduler import TraderSchedulerStatusResponse
from app.services.trader_scheduler import (
    TraderSchedulerBusyError,
    get_trader_scheduler_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["virtual-trader-scheduler"])


@router.get("/virtual-trader/scheduler-status", response_model=TraderSchedulerStatusResponse)
def get_virtual_trader_scheduler_status(
    log_limit: int = Query(8, ge=1, le=40),
) -> TraderSchedulerStatusResponse:
    """Return scheduler mode, cadence, run state, and recent run logs."""
    try:
        status = get_trader_scheduler_service().get_status(log_limit=log_limit)
        return TraderSchedulerStatusResponse(**status)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected scheduler status error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.get("/trader-status", response_model=TraderSchedulerStatusResponse)
def get_virtual_trader_scheduler_status_alias(
    log_limit: int = Query(8, ge=1, le=40),
) -> TraderSchedulerStatusResponse:
    """Alias endpoint kept for simpler external integrations."""
    return get_virtual_trader_scheduler_status(log_limit=log_limit)


@router.post("/virtual-trader/scheduler-run-now", response_model=TraderSchedulerStatusResponse)
def run_virtual_trader_scheduler_now(
    user_id: str | None = Query(default=None, min_length=1, max_length=120),
    log_limit: int = Query(8, ge=1, le=40),
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
        status = scheduler.get_status(log_limit=log_limit)
        return TraderSchedulerStatusResponse(**status)
    except TraderSchedulerBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected scheduler run-now error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc
