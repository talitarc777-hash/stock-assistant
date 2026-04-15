"""Monthly contribution record endpoints for user-configurable simulations."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.models.monthly_contribution import (
    MonthlyContributionCreateRequest,
    MonthlyContributionInitializeRequest,
    MonthlyContributionListResponse,
    MonthlyContributionUpdateRequest,
)
from app.services.account_ledger_service import (
    AccountLedgerError,
    get_account_ledger_service,
)
from app.services.monthly_contribution_service import (
    START_MONTH,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["monthly-contributions"])


@router.get("/monthly-contributions", response_model=MonthlyContributionListResponse)
def get_monthly_contributions(
    user_id: str = Query(..., min_length=1, max_length=120),
) -> MonthlyContributionListResponse:
    """Return immutable monthly contribution view from April 2026 onward."""
    try:
        records = get_account_ledger_service().build_monthly_contribution_view(user_id=user_id)
        return MonthlyContributionListResponse(
            user_id=user_id,
            start_month=START_MONTH,
            records=records,
        )
    except (ValueError, AccountLedgerError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected monthly contributions read error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.post("/monthly-contributions/initialize", response_model=MonthlyContributionListResponse)
def initialize_monthly_contributions(
    request: MonthlyContributionInitializeRequest,
) -> MonthlyContributionListResponse:
    """Initialize month rows from April 2026 (without creating cash events yet)."""
    try:
        records = get_account_ledger_service().build_monthly_contribution_view(user_id=request.user_id)
        return MonthlyContributionListResponse(
            user_id=request.user_id,
            start_month=START_MONTH,
            records=records,
        )
    except (ValueError, AccountLedgerError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected monthly contributions initialization error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.post("/monthly-contributions/update", response_model=MonthlyContributionListResponse)
def update_monthly_contributions(
    request: MonthlyContributionUpdateRequest,
) -> MonthlyContributionListResponse:
    """Legacy update endpoint kept for compatibility (immutable rows cannot be edited)."""
    try:
        raise AccountLedgerError(
            "Monthly contributions are immutable after creation. "
            "Use /monthly-contributions/create for new months and /virtual-account/deposit for additional cash."
        )
    except (ValueError, AccountLedgerError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected monthly contributions update error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.post("/monthly-contributions/create", response_model=MonthlyContributionListResponse)
def create_monthly_contributions(
    request: MonthlyContributionCreateRequest,
) -> MonthlyContributionListResponse:
    """Create immutable monthly contribution ledger events for specific months."""
    try:
        ledger = get_account_ledger_service()
        for record in request.records:
            ledger.create_monthly_contribution(
                user_id=request.user_id,
                month=record.month,
                amount=record.amount,
                source=request.source,
                reason="monthly contribution",
            )
        rows = ledger.build_monthly_contribution_view(user_id=request.user_id)
        return MonthlyContributionListResponse(
            user_id=request.user_id,
            start_month=START_MONTH,
            records=rows,
        )
    except (ValueError, AccountLedgerError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected monthly contributions create error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc
