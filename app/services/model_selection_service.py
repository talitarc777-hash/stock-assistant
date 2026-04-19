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
from app.services.model_lifecycle_service import (
    DEFAULT_PERIOD,
    DEFAULT_TARGET_NAME,
    get_model_lifecycle_service,
)
from app.services.model_results import list_compatible_saved_model_candidates
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
    """Discover saved trained models from the artifact directory.

    The model artifacts are stored under:
    ``data/models/<ticker>/<period>/<target_name>/<model_name>/...``

    We intentionally scan every discovered ``target_name`` folder so the web
    selector reflects both classification and regression models that already
    exist on disk, instead of assuming only one target type.
    """
    base_dir = Path(get_settings().research_models_dir)
    discovered: set[str] = set()
    if base_dir.exists():
        for evaluation_file in base_dir.glob("*/*/*/*/evaluation_table.csv"):
            model_name = evaluation_file.parent.name.strip().lower()
            if model_name:
                discovered.add(model_name)

    defaults = {
        "logistic_regression",
        "random_forest",
        "gradient_boosting",
        "linear_regression",
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


def resolve_selected_model_name(
    user_id: str | None = None,
    requested_model_name: str | None = None,
    ticker: str | None = None,
    period: str = DEFAULT_PERIOD,
    target_name: str = DEFAULT_TARGET_NAME,
) -> str:
    """Choose the effective model name for model and trader views."""
    clean_requested_model = (
        str(requested_model_name).strip().lower()
        if requested_model_name and str(requested_model_name).strip()
        else None
    )

    profile_model_name = None
    if user_id:
        profile_model_name = get_model_evaluation_settings(user_id=user_id).selected_model_name

    lifecycle = get_model_lifecycle_service()
    target_ticker = str(ticker).strip().upper() if ticker else "GLOBAL"
    production = lifecycle.get_production_model(
        ticker=target_ticker,
        period=period,
        target_name=target_name,
    )
    if production:
        return str(production["model_name"]).strip().lower()

    if target_ticker != "GLOBAL":
        shared_production = lifecycle.get_production_model(
            ticker="GLOBAL",
            period=period,
            target_name=target_name,
        )
        if shared_production:
            return str(shared_production["model_name"]).strip().lower()

    # Priority 2: use any compatible saved model artifact before trusting a
    # requested/profile model name. This avoids avoidable runtime misses.
    saved_candidates = list_compatible_saved_model_candidates(
        ticker=target_ticker,
        period=period,
        target_name=target_name,
        requested_model_name=None,
        limit=6,
    )
    if saved_candidates:
        selected_saved = str(saved_candidates[0]["model_name"]).strip().lower()
        logger.info(
            "Resolved model from saved artifacts ticker=%s period=%s target=%s model=%s source=%s",
            target_ticker,
            period,
            target_name,
            selected_saved,
            saved_candidates[0].get("source", "saved"),
        )
        return selected_saved

    # Priority 3: allow requested/profile model only when it is backed by at
    # least one compatible saved artifact.
    if clean_requested_model:
        requested_candidates = list_compatible_saved_model_candidates(
            ticker=target_ticker,
            period=period,
            target_name=target_name,
            requested_model_name=clean_requested_model,
            limit=20,
        )
        has_requested_artifact = any(
            str(item.get("model_name", "")).strip().lower() == clean_requested_model
            for item in requested_candidates
        )
        if has_requested_artifact:
            logger.info(
                "Resolved model from validated request ticker=%s period=%s target=%s model=%s",
                target_ticker,
                period,
                target_name,
                clean_requested_model,
            )
            return clean_requested_model
        logger.warning(
            "Requested model has no compatible saved artifacts ticker=%s period=%s target=%s requested=%s",
            target_ticker,
            period,
            target_name,
            clean_requested_model,
        )

    if profile_model_name:
        profile_candidates = list_compatible_saved_model_candidates(
            ticker=target_ticker,
            period=period,
            target_name=target_name,
            requested_model_name=profile_model_name,
            limit=20,
        )
        has_profile_artifact = any(
            str(item.get("model_name", "")).strip().lower() == profile_model_name
            for item in profile_candidates
        )
        if has_profile_artifact:
            return str(profile_model_name).strip().lower()
        logger.warning(
            "Profile-selected model has no compatible saved artifacts ticker=%s period=%s target=%s profile_model=%s",
            target_ticker,
            period,
            target_name,
            profile_model_name,
        )

    model_options = {item.model_name for item in list_available_model_options()}
    if DEFAULT_MODEL_NAME in model_options:
        return DEFAULT_MODEL_NAME
    if model_options:
        return sorted(model_options)[0]
    logger.warning(
        "No model options discovered for ticker=%s period=%s target=%s. Returning hardcoded default.",
        target_ticker,
        period,
        target_name,
    )
    return DEFAULT_MODEL_NAME
