"""Typed models for user-configurable monthly contribution records."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class MonthlyContributionRecordResponse(BaseModel):
    """One persisted monthly contribution record."""

    user_id: str
    month: str
    amount: float = Field(ge=0)
    created_at: str
    updated_at: str
    locked: bool = False
    applied_to_cash: bool = False

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str) -> str:
        text = str(value).strip()
        if len(text) != 7 or text[4] != "-":
            raise ValueError("month must use YYYY-MM format.")
        return text


class MonthlyContributionListResponse(BaseModel):
    """List response for a user's monthly contribution plan."""

    user_id: str
    start_month: str
    records: list[MonthlyContributionRecordResponse]
    deprecated: bool = False
    warning: str | None = None
    replacement_endpoint: str | None = None


class MonthlyContributionUpdateItem(BaseModel):
    """One row update for a monthly contribution amount."""

    month: str
    amount: float = Field(ge=0)

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str) -> str:
        text = str(value).strip()
        if len(text) != 7 or text[4] != "-":
            raise ValueError("month must use YYYY-MM format.")
        return text


class MonthlyContributionUpdateRequest(BaseModel):
    """Bulk update request for monthly contribution records."""

    user_id: str = Field(min_length=1, max_length=120)
    records: list[MonthlyContributionUpdateItem] = Field(min_length=1)


class MonthlyContributionInitializeRequest(BaseModel):
    """Request body to initialize monthly contribution records."""

    user_id: str = Field(min_length=1, max_length=120)


class MonthlyContributionCreateItem(BaseModel):
    """Create-only payload row for immutable monthly contributions."""

    month: str
    amount: float = Field(gt=0)

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str) -> str:
        text = str(value).strip()
        if len(text) != 7 or text[4] != "-":
            raise ValueError("month must use YYYY-MM format.")
        return text


class MonthlyContributionCreateRequest(BaseModel):
    """Create immutable monthly contribution records."""

    user_id: str = Field(min_length=1, max_length=120)
    records: list[MonthlyContributionCreateItem] = Field(min_length=1)
    source: str = Field(default="web", min_length=2, max_length=40)


class MonthlyContributionInputResponse(BaseModel):
    """Active recurring monthly contribution input for one profile."""

    user_id: str
    amount: float = Field(ge=0)
    effective_from_month: str
    created_at: str
    updated_at: str

    @field_validator("effective_from_month")
    @classmethod
    def validate_effective_from_month(cls, value: str) -> str:
        text = str(value).strip()
        if len(text) != 7 or text[4] != "-":
            raise ValueError("effective_from_month must use YYYY-MM format.")
        return text


class MonthlyContributionInputUpdateRequest(BaseModel):
    """Update request for recurring monthly contribution input."""

    user_id: str = Field(min_length=1, max_length=120)
    amount: float = Field(ge=0)
    source: str = Field(default="web", min_length=2, max_length=40)


class ModelEvaluationOptionResponse(BaseModel):
    """One available trained model option for UI selection."""

    model_name: str
    display_name: str


class ModelEvaluationSettingsResponse(BaseModel):
    """Persisted model evaluation settings for the web UI."""

    user_id: str
    selected_model_name: str
    available_models: list[ModelEvaluationOptionResponse]


class ModelEvaluationSettingsUpdateRequest(BaseModel):
    """Request body for selecting the active evaluation model."""

    user_id: str = Field(min_length=1, max_length=120)
    selected_model_name: str = Field(min_length=1, max_length=80)
