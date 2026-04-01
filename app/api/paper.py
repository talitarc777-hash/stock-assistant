"""API routes for simulation-only paper trading status."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.api_utils import PERIOD_PATTERN, TICKER_PATTERN, to_json_safe
from app.services.indicators import IndicatorInputError, add_technical_indicators
from app.services.market_data import EmptyDataError, InvalidTickerError, MarketDataError, get_price_history
from app.services.paper_simulator import PaperSimulationError, run_paper_simulation

logger = logging.getLogger(__name__)

router = APIRouter(tags=["paper-simulation"])


class PaperEventResponse(BaseModel):
    """One hypothetical paper event."""

    date: str
    event: str
    price: float
    quantity: float
    cash_after: float
    position_after: float
    realized_pnl: float
    note: str


class PaperStatusResponse(BaseModel):
    """Simulation-only paper status response."""

    ticker: str
    period: str
    mode: str
    latest_close: float
    initial_cash: float
    cash: float
    position_qty: float
    avg_entry_price: float | None
    position_market_value: float
    total_equity: float
    realized_pnl: float
    unrealized_pnl: float
    event_count: int
    latest_events: list[PaperEventResponse]


@router.get("/paper-status", response_model=PaperStatusResponse)
def paper_status(
    ticker: str = Query(
        ...,
        min_length=1,
        max_length=15,
        pattern=TICKER_PATTERN,
        description="Ticker symbol, e.g. VOO",
    ),
    period: str = Query(
        "5y",
        pattern=PERIOD_PATTERN,
        description="History period, e.g. 1y, 5y, max",
    ),
    initial_cash: float = Query(
        10_000.0,
        gt=0.0,
        description="Simulation starting cash. No real-money execution.",
    ),
) -> PaperStatusResponse:
    """
    Return simulation-only paper trading status.

    This endpoint is strictly informational and does not place real trades.
    """
    logger.info(
        "Request /paper-status ticker=%s period=%s initial_cash=%s",
        ticker,
        period,
        initial_cash,
    )
    try:
        price_df = get_price_history(ticker=ticker, period=period)
        indicators_df = add_technical_indicators(price_df)
        simulation = run_paper_simulation(
            ticker=ticker,
            indicators_df=indicators_df,
            initial_cash=initial_cash,
        )
    except InvalidTickerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except EmptyDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (IndicatorInputError, PaperSimulationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error in /paper-status")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc

    latest_close = float(indicators_df.iloc[-1]["close"])
    latest_events = simulation.events[-20:]

    return PaperStatusResponse(
        ticker=simulation.ticker,
        period=period,
        mode="simulation_only_no_real_money_no_broker_execution",
        latest_close=float(to_json_safe(latest_close)),
        initial_cash=float(to_json_safe(simulation.initial_cash)),
        cash=float(to_json_safe(simulation.cash)),
        position_qty=float(to_json_safe(simulation.position_qty)),
        avg_entry_price=to_json_safe(simulation.avg_entry_price),
        position_market_value=float(to_json_safe(simulation.position_market_value)),
        total_equity=float(to_json_safe(simulation.total_equity)),
        realized_pnl=float(to_json_safe(simulation.realized_pnl)),
        unrealized_pnl=float(to_json_safe(simulation.unrealized_pnl)),
        event_count=len(simulation.events),
        latest_events=[
            PaperEventResponse(
                date=item.date,
                event=item.event,
                price=float(to_json_safe(item.price)),
                quantity=float(to_json_safe(item.quantity)),
                cash_after=float(to_json_safe(item.cash_after)),
                position_after=float(to_json_safe(item.position_after)),
                realized_pnl=float(to_json_safe(item.realized_pnl)),
                note=item.note,
            )
            for item in latest_events
        ],
    )

