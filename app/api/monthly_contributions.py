"""Monthly contribution record endpoints for user-configurable simulations."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.models.monthly_contribution import (
    MonthlyContributionInitializeRequest,
    MonthlyContributionListResponse,
    MonthlyContributionUpdateRequest,
)
from app.services.monthly_contribution_service import (
    START_MONTH,
    get_monthly_contribution_store,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["monthly-contributions"])


@router.get("/monthly-contributions", response_model=MonthlyContributionListResponse)
def get_monthly_contributions(
    user_id: str = Query(..., min_length=1, max_length=120),
) -> MonthlyContributionListResponse:
    """Return all monthly contribution records for a user, auto-initialized from April 2026."""
    try:
        records = get_monthly_contribution_store().list_records(user_id=user_id)
        return MonthlyContributionListResponse(
            user_id=user_id,
            start_month=START_MONTH,
            records=records,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected monthly contributions read error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.post("/monthly-contributions/initialize", response_model=MonthlyContributionListResponse)
def initialize_monthly_contributions(
    request: MonthlyContributionInitializeRequest,
) -> MonthlyContributionListResponse:
    """Initialize monthly contribution records from April 2026 to the current month."""
    try:
        records = get_monthly_contribution_store().initialize_for_user(request.user_id)
        return MonthlyContributionListResponse(
            user_id=request.user_id,
            start_month=START_MONTH,
            records=records,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected monthly contributions initialization error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.post("/monthly-contributions/update", response_model=MonthlyContributionListResponse)
def update_monthly_contributions(
    request: MonthlyContributionUpdateRequest,
) -> MonthlyContributionListResponse:
    """Update one or more monthly contribution amounts for a user."""
    try:
        store = get_monthly_contribution_store()
        for record in request.records:
            store.update_amount(
                user_id=request.user_id,
                month=record.month,
                amount=record.amount,
            )
        records = store.list_records(request.user_id)
        return MonthlyContributionListResponse(
            user_id=request.user_id,
            start_month=START_MONTH,
            records=records,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected monthly contributions update error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc
