"""Immutable virtual account endpoints (cash ledger + derived account view)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.models.account_ledger import (
    AccountLedgerListResponse,
    VirtualAccountDepositRequest,
    VirtualAccountDiagnosticsResponse,
    VirtualAccountResetRequest,
    VirtualAccountResetResponse,
    VirtualAccountSummaryResponse,
    VirtualAccountWithdrawalRequest,
)
from app.services.account_ledger_service import (
    AccountLedgerError,
    get_account_ledger_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["virtual-account"])


@router.get("/virtual-account/summary", response_model=VirtualAccountSummaryResponse)
def virtual_account_summary(
    user_id: str = Query(..., min_length=1, max_length=120),
) -> VirtualAccountSummaryResponse:
    """Return current account state rebuilt from immutable ledger events."""
    try:
        payload = get_account_ledger_service().build_account_summary(user_id=user_id)
        return VirtualAccountSummaryResponse(**payload)
    except AccountLedgerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected virtual-account summary error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.get("/virtual-account/ledger", response_model=AccountLedgerListResponse)
def virtual_account_ledger(
    user_id: str = Query(..., min_length=1, max_length=120),
    limit: int = Query(200, ge=1, le=2000),
) -> AccountLedgerListResponse:
    """List immutable ledger events for one user."""
    try:
        events = get_account_ledger_service().list_events(user_id=user_id, limit=limit)
        return AccountLedgerListResponse(
            user_id=user_id,
            count=len(events),
            events=events,
        )
    except AccountLedgerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected virtual-account ledger error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.post("/virtual-account/deposit", response_model=VirtualAccountSummaryResponse)
def virtual_account_deposit(request: VirtualAccountDepositRequest) -> VirtualAccountSummaryResponse:
    """Create an immutable manual deposit event and return updated account summary."""
    try:
        ledger = get_account_ledger_service()
        ledger.create_manual_deposit(
            user_id=request.user_id,
            amount=request.amount,
            source=request.source,
            reason=request.reason,
        )
        return VirtualAccountSummaryResponse(**ledger.build_account_summary(request.user_id))
    except AccountLedgerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected virtual-account deposit error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.post("/virtual-account/withdraw", response_model=VirtualAccountSummaryResponse)
def virtual_account_withdraw(request: VirtualAccountWithdrawalRequest) -> VirtualAccountSummaryResponse:
    """Create an immutable withdrawal event and return updated account summary."""
    try:
        ledger = get_account_ledger_service()
        ledger.create_withdrawal(
            user_id=request.user_id,
            amount=request.amount,
            source=request.source,
            reason=request.reason,
        )
        return VirtualAccountSummaryResponse(**ledger.build_account_summary(request.user_id))
    except AccountLedgerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected virtual-account withdrawal error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.get("/virtual-account/diagnostics", response_model=VirtualAccountDiagnosticsResponse)
def virtual_account_diagnostics(
    user_id: str = Query(..., min_length=1, max_length=120),
) -> VirtualAccountDiagnosticsResponse:
    """Return profile-scoped persistence diagnostics."""
    try:
        payload = get_account_ledger_service().get_profile_diagnostics(user_id=user_id)
        return VirtualAccountDiagnosticsResponse(**payload)
    except AccountLedgerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected virtual-account diagnostics error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.post("/virtual-account/reset", response_model=VirtualAccountResetResponse)
def virtual_account_reset(request: VirtualAccountResetRequest) -> VirtualAccountResetResponse:
    """Reset one profile's simulated trading account data only."""
    if not bool(request.confirm_reset):
        raise HTTPException(
            status_code=400,
            detail="confirm_reset must be true to run a destructive account reset.",
        )
    try:
        payload = get_account_ledger_service().reset_profile_account_data(
            user_id=request.user_id,
            reset_monthly_contributions=bool(request.reset_monthly_contributions),
        )
        return VirtualAccountResetResponse(**payload)
    except AccountLedgerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected virtual-account reset error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc
