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

DEPRECATION_WARNING = (
    "This endpoint is deprecated. "
    "Use GET/POST /virtual-account/monthly-contribution-input for the recurring monthly amount."
)
DEPRECATION_REPLACEMENT = "/virtual-account/monthly-contribution-input"


def _deprecated_response(user_id: str) -> MonthlyContributionListResponse:
    """Compatibility response for deprecated monthly-record endpoints.

    This intentionally avoids mutating legacy monthly-plan tables so the new
    recurring monthly input remains the primary source of truth.
    """
    rows = get_account_ledger_service().list_monthly_contribution_records(user_id)
    records = [
        {
            "user_id": user_id,
            "month": row["month"],
            "amount": float(row["amount"]),
            "created_at": row.get("created_at") or "",
            "updated_at": row.get("created_at") or "",
            "locked": True,
            "applied_to_cash": True,
        }
        for row in rows
    ]
    return MonthlyContributionListResponse(
        user_id=user_id,
        start_month=START_MONTH,
        records=records,
        deprecated=True,
        warning=DEPRECATION_WARNING,
        replacement_endpoint=DEPRECATION_REPLACEMENT,
    )


@router.get("/monthly-contributions", response_model=MonthlyContributionListResponse)
def get_monthly_contributions(
    user_id: str = Query(..., min_length=1, max_length=120),
) -> MonthlyContributionListResponse:
    """Deprecated compatibility endpoint for monthly records."""
    try:
        logger.warning(
            "Deprecated endpoint called path=/monthly-contributions user_id=%s replacement=%s",
            user_id,
            DEPRECATION_REPLACEMENT,
        )
        return _deprecated_response(user_id=user_id)
    except (ValueError, AccountLedgerError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected monthly contributions read error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.post("/monthly-contributions/initialize", response_model=MonthlyContributionListResponse)
def initialize_monthly_contributions(
    request: MonthlyContributionInitializeRequest,
) -> MonthlyContributionListResponse:
    """Deprecated no-op endpoint kept for backward compatibility."""
    try:
        logger.warning(
            "Deprecated endpoint called path=/monthly-contributions/initialize user_id=%s replacement=%s",
            request.user_id,
            DEPRECATION_REPLACEMENT,
        )
        return _deprecated_response(user_id=request.user_id)
    except (ValueError, AccountLedgerError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected monthly contributions initialization error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.post("/monthly-contributions/update", response_model=MonthlyContributionListResponse)
def update_monthly_contributions(
    request: MonthlyContributionUpdateRequest,
) -> MonthlyContributionListResponse:
    """Deprecated no-op endpoint kept for backward compatibility."""
    try:
        logger.warning(
            "Deprecated endpoint called path=/monthly-contributions/update user_id=%s replacement=%s",
            request.user_id,
            DEPRECATION_REPLACEMENT,
        )
        return _deprecated_response(user_id=request.user_id)
    except (ValueError, AccountLedgerError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected monthly contributions update error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.post("/monthly-contributions/create", response_model=MonthlyContributionListResponse)
def create_monthly_contributions(
    request: MonthlyContributionCreateRequest,
) -> MonthlyContributionListResponse:
    """Deprecated no-op endpoint kept for backward compatibility."""
    try:
        logger.warning(
            "Deprecated endpoint called path=/monthly-contributions/create user_id=%s replacement=%s",
            request.user_id,
            DEPRECATION_REPLACEMENT,
        )
        return _deprecated_response(user_id=request.user_id)
    except (ValueError, AccountLedgerError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected monthly contributions create error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc
