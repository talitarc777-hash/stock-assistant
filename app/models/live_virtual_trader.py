"""Typed API models for live virtual trader endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LiveTraderRunRequest(BaseModel):
    """Request body for running live simulated trader now."""

    user_id: str = Field(min_length=1, max_length=120)
    tickers: list[str] | None = None
    model_name: str | None = Field(default=None, min_length=1, max_length=80)
    auto_run: bool = True


class LiveTraderDecisionResponse(BaseModel):
    timestamp: str
    user_id: str
    ticker: str
    action: str
    quantity: float
    price: float
    model_name: str
    confidence_score: float | None = None
    reason: str
    threshold_summary: str
    technical_state_summary: str
    news_sentiment_summary: str
    benchmark_strength_summary: str
    action_summary: str
    cash_after: float
    holdings_after: float
    realized_pnl: float
    unrealized_pnl: float
    metadata: dict | None = None


class LiveTraderHoldingResponse(BaseModel):
    user_id: str | None = None
    ticker: str
    quantity: float
    avg_entry_price: float
    entry_timestamp: str | None = None
    model_name: str | None = None
    updated_at: str | None = None
    current_price: float
    market_value: float
    unrealized_pnl: float


class LiveTraderContributionEventResponse(BaseModel):
    user_id: str | None = None
    month: str | None = None
    configured_amount: float | None = None
    applied_amount: float | None = None
    delta_applied_now: float | None = None
    applied_at: str | None = None
    event_type: str | None = None
    amount: float | None = None
    created_at: str | None = None


class LiveTraderAccountResponse(BaseModel):
    cash: float
    realized_pnl: float
    total_contributions_applied: float
    holdings_value: float
    total_equity: float


class LiveTraderStatusResponse(BaseModel):
    user_id: str
    model_name: str
    generated_at_utc: str
    account: LiveTraderAccountResponse
    holdings: list[LiveTraderHoldingResponse]
    latest_decisions: list[LiveTraderDecisionResponse]
    contribution_events: list[dict]


class LiveTraderTradesResponse(BaseModel):
    user_id: str
    count: int
    trades: list[LiveTraderDecisionResponse]
    contribution_application_history: list[dict]
