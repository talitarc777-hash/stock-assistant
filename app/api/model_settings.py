"""Model evaluation settings endpoints for the web dashboard."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.models.monthly_contribution import (
    ModelEvaluationSettingsResponse,
    ModelEvaluationSettingsUpdateRequest,
)
from app.services.model_selection_service import (
    get_model_evaluation_settings,
    update_model_evaluation_settings,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["model-settings"])


@router.get("/model-evaluation/settings", response_model=ModelEvaluationSettingsResponse)
def get_model_settings(
    user_id: str = Query(..., min_length=1, max_length=120),
) -> ModelEvaluationSettingsResponse:
    """Return the selected evaluation model and the available saved models."""
    try:
        return get_model_evaluation_settings(user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected model settings read error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc


@router.post("/model-evaluation/settings", response_model=ModelEvaluationSettingsResponse)
def update_model_settings(
    request: ModelEvaluationSettingsUpdateRequest,
) -> ModelEvaluationSettingsResponse:
    """Persist the selected evaluation model for one shared user profile."""
    try:
        return update_model_evaluation_settings(
            user_id=request.user_id,
            selected_model_name=request.selected_model_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected model settings update error")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc
