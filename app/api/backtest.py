"""API routes for strategy backtesting."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.backtest.engine import BacktestInputError, run_backtest
from app.core.api_utils import PERIOD_PATTERN, TICKER_PATTERN, to_json_safe, to_json_safe_dict
from app.services.indicators import IndicatorInputError, add_technical_indicators
from app.services.market_data import (
    EmptyDataError,
    InvalidTickerError,
    MarketDataError,
    get_price_history,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["backtest"])


class BacktestMetricsResponse(BaseModel):
    """Backtest metrics summary."""

    total_return_pct: float
    cagr_pct: float
    max_drawdown_pct: float
    win_rate_pct: float
    number_of_trades: int
    average_trade_return_pct: float
    buy_and_hold_return_pct: float
    transaction_cost_pct: float


class TradeLogRow(BaseModel):
    """One trade row in preview output."""

    entry_date: str
    entry_price: float | None
    exit_date: str
    exit_price: float | None
    return_pct: float | None
    exit_reason: str


class EquityCurvePoint(BaseModel):
    """One point on equity curve."""

    date: str
    equity: float | None


class BacktestResponse(BaseModel):
    """Response model for /backtest."""

    ticker: str
    period: str
    metrics_summary: BacktestMetricsResponse
    trade_log_preview: list[TradeLogRow]
    equity_curve: list[EquityCurvePoint]


@router.get("/backtest", response_model=BacktestResponse)
def backtest_ticker(
    ticker: str = Query(
        ...,
        min_length=1,
        max_length=15,
        pattern=TICKER_PATTERN,
        description="Ticker symbol, e.g. VOO",
    ),
    period: str = Query(
        "10y",
        pattern=PERIOD_PATTERN,
        description="History period, e.g. 5y, 10y, max",
    ),
    transaction_cost_pct: float = Query(
        0.0,
        ge=0.0,
        description="Optional one-way transaction cost in decimal form (e.g. 0.001 = 0.1%).",
    ),
) -> BacktestResponse:
    """Run the strategy backtest on one ticker using daily data."""
    logger.info(
        "Request /backtest ticker=%s period=%s transaction_cost_pct=%s",
        ticker,
        period,
        transaction_cost_pct,
    )
    try:
        price_df = get_price_history(ticker=ticker, period=period)
        indicators_df = add_technical_indicators(price_df)
        result = run_backtest(
            df=indicators_df,
            transaction_cost_pct=transaction_cost_pct,
        )
    except InvalidTickerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except EmptyDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (IndicatorInputError, BacktestInputError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error in /backtest")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc

    trade_log_preview = [
        TradeLogRow(
            entry_date=trade.entry_date,
            entry_price=to_json_safe(trade.entry_price),
            exit_date=trade.exit_date,
            exit_price=to_json_safe(trade.exit_price),
            return_pct=to_json_safe(trade.return_pct),
            exit_reason=trade.exit_reason,
        )
        for trade in result.trades[-20:]
    ]

    equity_curve = [
        EquityCurvePoint(
            date=point["date"],
            equity=to_json_safe(point["equity"]),
        )
        for point in result.equity_curve
    ]

    return BacktestResponse(
        ticker=ticker.strip().upper(),
        period=period,
        metrics_summary=BacktestMetricsResponse(**to_json_safe_dict(result.metrics)),
        trade_log_preview=trade_log_preview,
        equity_curve=equity_curve,
    )
