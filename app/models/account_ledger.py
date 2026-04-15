"""Typed models for immutable virtual account ledger endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


LEDGER_EVENT_TYPES = {
    "monthly_contribution",
    "manual_deposit",
    "withdrawal",
    "buy_trade",
    "sell_trade",
    "fee",
}


class AccountLedgerEventResponse(BaseModel):
    """One immutable virtual account ledger event."""

    id: int
    user_id: str
    event_type: str
    amount: float
    ticker: str | None = None
    quantity: float | None = None
    price: float | None = None
    reason: str | None = None
    source: str | None = None
    reference_month: str | None = None
    created_at: str
    metadata: dict = Field(default_factory=dict)


class AccountLedgerListResponse(BaseModel):
    """Ledger list response for one user."""

    user_id: str
    count: int
    events: list[AccountLedgerEventResponse]


class VirtualHoldingResponse(BaseModel):
    """Derived holding state from immutable buy/sell ledger events."""

    ticker: str
    quantity: float
    avg_entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float


class VirtualAccountSummaryResponse(BaseModel):
    """Derived account summary rebuilt from immutable ledger history."""

    user_id: str
    as_of: str
    cash: float
    holdings_value: float
    total_account_value: float
    realized_pnl: float
    unrealized_pnl: float
    net_deposits: float
    holdings: list[VirtualHoldingResponse]
    latest_prices: dict[str, float]


class VirtualAccountDepositRequest(BaseModel):
    """Request payload to create a manual deposit event."""

    user_id: str = Field(min_length=1, max_length=120)
    amount: float = Field(gt=0)
    reason: str | None = Field(default=None, max_length=200)
    source: str = Field(default="web", min_length=2, max_length=40)


class VirtualAccountWithdrawalRequest(BaseModel):
    """Request payload to create a withdrawal event."""

    user_id: str = Field(min_length=1, max_length=120)
    amount: float = Field(gt=0)
    reason: str | None = Field(default=None, max_length=200)
    source: str = Field(default="web", min_length=2, max_length=40)


class MonthlyContributionCreateRequest(BaseModel):
    """Create-only monthly contribution event request."""

    user_id: str = Field(min_length=1, max_length=120)
    month: str = Field(min_length=7, max_length=7)
    amount: float = Field(gt=0)
    source: str = Field(default="web", min_length=2, max_length=40)
    reason: str | None = Field(default=None, max_length=200)

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str) -> str:
        text = str(value).strip()
        if len(text) != 7 or text[4] != "-":
            raise ValueError("month must use YYYY-MM format.")
        return text
