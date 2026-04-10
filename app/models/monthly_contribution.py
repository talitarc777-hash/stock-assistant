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
