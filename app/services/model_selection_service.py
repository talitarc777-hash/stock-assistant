"""Helpers for persisted model-evaluation selection in the web UI."""

from __future__ import annotations

import logging
from pathlib import Path

from app.core.settings import get_settings
from app.models.monthly_contribution import (
    ModelEvaluationOptionResponse,
    ModelEvaluationSettingsResponse,
)
from app.models.user_profile import UserProfileSettingsUpdateRequest
from app.services.user_profile_service import get_user_profile_store

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "logistic_regression"
DISPLAY_NAME_MAP = {
    "logistic_regression": "Logistic Regression",
    "random_forest": "Random Forest",
    "gradient_boosting": "Gradient Boosting",
    "linear_regression": "Linear Regression",
}


def _scan_saved_model_names() -> list[str]:
    """Discover saved trained models from the artifact directory."""
    base_dir = Path(get_settings().research_models_dir)
    discovered: set[str] = set()
    if base_dir.exists():
        for evaluation_file in base_dir.glob("*/*/target_5d_updown/*/evaluation_table.csv"):
            model_name = evaluation_file.parent.name.strip().lower()
            if model_name:
                discovered.add(model_name)

    defaults = {
        "logistic_regression",
        "random_forest",
        "gradient_boosting",
    }
    return sorted(discovered | defaults)


def list_available_model_options() -> list[ModelEvaluationOptionResponse]:
    """Return human-friendly model options for the frontend selector."""
    return [
        ModelEvaluationOptionResponse(
            model_name=model_name,
            display_name=DISPLAY_NAME_MAP.get(
                model_name,
                model_name.replace("_", " ").title(),
            ),
        )
        for model_name in _scan_saved_model_names()
    ]


def get_model_evaluation_settings(user_id: str) -> ModelEvaluationSettingsResponse:
    """Return the persisted selected model and the available saved models."""
    profile = get_user_profile_store().get_or_create_profile(user_id=user_id)
    options = list_available_model_options()
    valid_names = {item.model_name for item in options}
    selected_model_name = profile.selected_evaluation_model or DEFAULT_MODEL_NAME
    if selected_model_name not in valid_names:
        selected_model_name = DEFAULT_MODEL_NAME
    return ModelEvaluationSettingsResponse(
        user_id=profile.user_id,
        selected_model_name=selected_model_name,
        available_models=options,
    )


def update_model_evaluation_settings(user_id: str, selected_model_name: str) -> ModelEvaluationSettingsResponse:
    """Persist the selected model name into the shared profile store."""
    clean_model_name = str(selected_model_name).strip().lower()
    valid_names = {item.model_name for item in list_available_model_options()}
    if clean_model_name not in valid_names:
        raise ValueError(
            f"Unsupported model selection: {selected_model_name}. "
            f"Available models: {', '.join(sorted(valid_names))}."
        )
    get_user_profile_store().update_profile_settings(
        UserProfileSettingsUpdateRequest(
            user_id=user_id,
            selected_evaluation_model=clean_model_name,
            last_active_source="dashboard",
        )
    )
    logger.info("Updated model evaluation selection user_id=%s model=%s", user_id, clean_model_name)
    return get_model_evaluation_settings(user_id=user_id)


def resolve_selected_model_name(user_id: str | None = None, requested_model_name: str | None = None) -> str:
    """Choose the effective model name for model and trader views."""
    if requested_model_name:
        return str(requested_model_name).strip().lower()
    if user_id:
        return get_model_evaluation_settings(user_id=user_id).selected_model_name
    return DEFAULT_MODEL_NAME
