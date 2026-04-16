"""Universe endpoints for broader ticker coverage management."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.universe_service import get_active_universe

router = APIRouter(tags=["universe"])


class UniverseResponse(BaseModel):
    source: str
    count: int
    tickers: list[str]


@router.get("/universe/tickers", response_model=UniverseResponse)
def universe_tickers(
    limit: int = Query(200, ge=1, le=5000),
) -> UniverseResponse:
    """Return a capped U.S. ticker universe list for training/simulation jobs."""
    tickers = get_active_universe(limit=limit)
    return UniverseResponse(source="active_us_universe", count=len(tickers), tickers=tickers)
