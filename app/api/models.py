"""Read-only API routes for saved model predictions and virtual trader results."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.api_utils import PERIOD_PATTERN, TICKER_PATTERN, to_json_safe, to_json_safe_dict
from app.services.model_results import (
    ModelResultsError,
    load_model_accuracy_summary,
    load_model_history,
    load_model_latest_prediction,
    load_virtual_trader_summary,
    load_virtual_trader_trades,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["models"])


class ModelPredictionPointResponse(BaseModel):
    """One saved model prediction row with explanation fields."""

    prediction_date: str
    ticker: str
    predicted_value: float | int | None
    confidence_score: float | None
    actual_future_result: float | int | None
    hit_miss: str
    model_name: str
    target_name: str
    task_type: str
    evaluation_window: int
    technical_state_summary: str
    news_sentiment_summary: str
    benchmark_strength_summary: str
    explanation: str


class RollingAccuracyPointResponse(BaseModel):
    """One rolling accuracy point for charting."""

    date: str
    rolling_accuracy: float | None


class FoldSizeResponse(BaseModel):
    """One walk-forward fold size summary."""

    fold: int
    train_rows: int
    test_rows: int


class ModelMetricValuesResponse(BaseModel):
    """Flexible metric values for classification or regression output."""

    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    positive_rate_actual: float | None = None
    positive_rate_predicted: float | None = None
    mae: float | None = None
    rmse: float | None = None
    r2: float | None = None
    direction_accuracy: float | None = None


class ModelAccuracyMetricsResponse(BaseModel):
    """Saved walk-forward metric summary."""

    generated_at_utc: str
    ticker: str
    period: str
    target_name: str
    task_type: str
    model_name: str
    row_count: int
    feature_count: int
    time_series_splits: int
    validation_method: str
    validation_note: str
    fold_sizes: list[FoldSizeResponse]
    metrics: ModelMetricValuesResponse


class ModelLatestResponse(BaseModel):
    """Latest saved model prediction."""

    ticker: str
    period: str
    target_name: str
    model_name: str
    latest_prediction: ModelPredictionPointResponse


class ModelHistoryResponse(BaseModel):
    """Historical saved model predictions and rolling accuracy."""

    ticker: str
    period: str
    target_name: str
    model_name: str
    count: int
    history: list[ModelPredictionPointResponse]
    rolling_accuracy: list[RollingAccuracyPointResponse]


class ModelAccuracyResponse(BaseModel):
    """Saved metrics plus latest rolling accuracy."""

    ticker: str
    period: str
    target_name: str
    model_name: str
    latest_rolling_accuracy: float | None
    metrics_summary: ModelAccuracyMetricsResponse
    rolling_accuracy: list[RollingAccuracyPointResponse]


class VirtualTraderEquityPointResponse(BaseModel):
    """One equity curve point from the virtual trader."""

    date: str
    cash: float
    holdings_value: float
    total_equity: float
    realized_pnl: float
    unrealized_pnl: float
    benchmark_equity: float


class VirtualTraderSummaryDataResponse(BaseModel):
    """Summary statistics for a virtual trader run."""

    generated_at_utc: str
    ticker: str
    period: str
    model_name: str
    mode: str
    task_type: str
    monthly_contribution_usd: float
    initial_cash: float
    confidence_threshold: float
    max_position_size_pct: float
    stop_loss_pct: float
    take_profit_pct: float | None
    total_contributions: float
    cash: float
    holdings: float
    entry_price: float | None
    exit_price: float | None
    realized_pnl: float
    unrealized_pnl: float
    final_equity: float
    return_on_contributions_pct: float
    trade_count: int
    benchmark_symbol: str
    benchmark_final_equity: float
    outperformance_vs_benchmark_pct_points: float


class VirtualTraderBenchmarkResponse(BaseModel):
    """Benchmark comparison for the virtual trader."""

    benchmark: str
    final_equity: float
    total_contributions: float
    return_on_contributions_pct: float


class VirtualTraderSummaryResponse(BaseModel):
    """Summary endpoint for virtual trader results."""

    ticker: str
    period: str
    model_name: str
    summary: VirtualTraderSummaryDataResponse
    benchmark_comparison: VirtualTraderBenchmarkResponse
    equity_curve: list[VirtualTraderEquityPointResponse]


class VirtualTraderTradeResponse(BaseModel):
    """One virtual trader trade log row."""

    timestamp: str
    ticker: str
    action: str
    price: float
    quantity: float
    cash_after: float
    holdings_after: float
    entry_price: float | None
    exit_price: float | None
    position_size_value: float
    realized_pnl: float
    unrealized_pnl: float
    model_confidence: float | None
    trade_reason: str
    threshold_summary: str
    action_summary: str
    technical_state_summary: str
    news_sentiment_summary: str
    benchmark_strength_summary: str
    prediction_explanation: str
    explanation: str


class MonthlyContributionResponse(BaseModel):
    """One monthly contribution record."""

    date: str
    amount: float
    cumulative_contributions: float


class VirtualTraderTradesResponse(BaseModel):
    """Trade-log endpoint for virtual trader results."""

    ticker: str
    period: str
    model_name: str
    trade_count: int
    trade_log: list[VirtualTraderTradeResponse]
    monthly_contributions: list[MonthlyContributionResponse]


def _build_metric_values_response(payload: dict) -> ModelMetricValuesResponse:
    """Convert saved metric dictionary into a typed response model."""
    return ModelMetricValuesResponse(**to_json_safe_dict(payload))


@router.get("/model-latest", response_model=ModelLatestResponse)
def model_latest(
    ticker: str = Query(..., min_length=1, max_length=15, pattern=TICKER_PATTERN),
    period: str = Query("5y", pattern=PERIOD_PATTERN),
    target_name: str = Query("target_5d_updown", min_length=1, max_length=50),
    model_name: str = Query("logistic_regression", min_length=1, max_length=50),
) -> ModelLatestResponse:
    """Return the latest saved model prediction row for one ticker."""
    logger.info(
        "Request /model-latest ticker=%s period=%s target=%s model=%s",
        ticker,
        period,
        target_name,
        model_name,
    )
    try:
        payload = load_model_latest_prediction(
            ticker=ticker,
            period=period,
            target_name=target_name,
            model_name=model_name,
        )
    except ModelResultsError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error in /model-latest")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc

    latest = ModelPredictionPointResponse(**to_json_safe_dict(payload["latest"]))
    return ModelLatestResponse(
        ticker=payload["ticker"],
        period=payload["period"],
        target_name=payload["target_name"],
        model_name=payload["model_name"],
        latest_prediction=latest,
    )


@router.get("/model-history", response_model=ModelHistoryResponse)
def model_history(
    ticker: str = Query(..., min_length=1, max_length=15, pattern=TICKER_PATTERN),
    period: str = Query("5y", pattern=PERIOD_PATTERN),
    target_name: str = Query("target_5d_updown", min_length=1, max_length=50),
    model_name: str = Query("logistic_regression", min_length=1, max_length=50),
    limit: int = Query(200, ge=1, le=5000),
) -> ModelHistoryResponse:
    """Return saved model prediction history and rolling accuracy for one ticker."""
    logger.info(
        "Request /model-history ticker=%s period=%s target=%s model=%s limit=%s",
        ticker,
        period,
        target_name,
        model_name,
        limit,
    )
    try:
        payload = load_model_history(
            ticker=ticker,
            period=period,
            target_name=target_name,
            model_name=model_name,
            limit=limit,
        )
    except ModelResultsError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error in /model-history")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc

    return ModelHistoryResponse(
        ticker=payload["ticker"],
        period=payload["period"],
        target_name=payload["target_name"],
        model_name=payload["model_name"],
        count=payload["count"],
        history=[ModelPredictionPointResponse(**to_json_safe_dict(item)) for item in payload["history"]],
        rolling_accuracy=[
            RollingAccuracyPointResponse(**to_json_safe_dict(item)) for item in payload["rolling_accuracy"]
        ],
    )


@router.get("/model-accuracy", response_model=ModelAccuracyResponse)
def model_accuracy(
    ticker: str = Query(..., min_length=1, max_length=15, pattern=TICKER_PATTERN),
    period: str = Query("5y", pattern=PERIOD_PATTERN),
    target_name: str = Query("target_5d_updown", min_length=1, max_length=50),
    model_name: str = Query("logistic_regression", min_length=1, max_length=50),
    window: int = Query(20, ge=1, le=252),
) -> ModelAccuracyResponse:
    """Return saved walk-forward metrics and rolling accuracy."""
    logger.info(
        "Request /model-accuracy ticker=%s period=%s target=%s model=%s window=%s",
        ticker,
        period,
        target_name,
        model_name,
        window,
    )
    try:
        payload = load_model_accuracy_summary(
            ticker=ticker,
            period=period,
            target_name=target_name,
            model_name=model_name,
            window=window,
        )
    except ModelResultsError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error in /model-accuracy")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc

    metrics_payload = payload["metrics"]
    metrics_response = ModelAccuracyMetricsResponse(
        generated_at_utc=metrics_payload["generated_at_utc"],
        ticker=metrics_payload["ticker"],
        period=metrics_payload["period"],
        target_name=metrics_payload["target_name"],
        task_type=metrics_payload["task_type"],
        model_name=metrics_payload["model_name"],
        row_count=int(metrics_payload["row_count"]),
        feature_count=int(metrics_payload["feature_count"]),
        time_series_splits=int(metrics_payload["time_series_splits"]),
        validation_method=metrics_payload["validation_method"],
        validation_note=metrics_payload["validation_note"],
        fold_sizes=[FoldSizeResponse(**to_json_safe_dict(item)) for item in metrics_payload["fold_sizes"]],
        metrics=_build_metric_values_response(metrics_payload["metrics"]),
    )

    return ModelAccuracyResponse(
        ticker=payload["ticker"],
        period=payload["period"],
        target_name=payload["target_name"],
        model_name=payload["model_name"],
        latest_rolling_accuracy=to_json_safe(payload["latest_rolling_accuracy"]),
        metrics_summary=metrics_response,
        rolling_accuracy=[
            RollingAccuracyPointResponse(**to_json_safe_dict(item)) for item in payload["rolling_accuracy"]
        ],
    )


@router.get("/virtual-trader-summary", response_model=VirtualTraderSummaryResponse)
def virtual_trader_summary(
    ticker: str = Query(..., min_length=1, max_length=15, pattern=TICKER_PATTERN),
    period: str = Query("5y", pattern=PERIOD_PATTERN),
    model_name: str = Query("logistic_regression", min_length=1, max_length=50),
    equity_limit: int = Query(500, ge=1, le=5000),
) -> VirtualTraderSummaryResponse:
    """Return saved virtual trader summary and equity curve."""
    logger.info(
        "Request /virtual-trader-summary ticker=%s period=%s model=%s equity_limit=%s",
        ticker,
        period,
        model_name,
        equity_limit,
    )
    try:
        payload = load_virtual_trader_summary(
            ticker=ticker,
            period=period,
            model_name=model_name,
            equity_limit=equity_limit,
        )
    except ModelResultsError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error in /virtual-trader-summary")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc

    return VirtualTraderSummaryResponse(
        ticker=payload["ticker"],
        period=payload["period"],
        model_name=payload["model_name"],
        summary=VirtualTraderSummaryDataResponse(**to_json_safe_dict(payload["summary"])),
        benchmark_comparison=VirtualTraderBenchmarkResponse(
            **to_json_safe_dict(payload["benchmark_comparison"])
        ),
        equity_curve=[
            VirtualTraderEquityPointResponse(**to_json_safe_dict(item)) for item in payload["equity_curve"]
        ],
    )


@router.get("/virtual-trader-trades", response_model=VirtualTraderTradesResponse)
def virtual_trader_trades(
    ticker: str = Query(..., min_length=1, max_length=15, pattern=TICKER_PATTERN),
    period: str = Query("5y", pattern=PERIOD_PATTERN),
    model_name: str = Query("logistic_regression", min_length=1, max_length=50),
    limit: int = Query(200, ge=1, le=5000),
) -> VirtualTraderTradesResponse:
    """Return saved virtual trader trade log and monthly contributions."""
    logger.info(
        "Request /virtual-trader-trades ticker=%s period=%s model=%s limit=%s",
        ticker,
        period,
        model_name,
        limit,
    )
    try:
        payload = load_virtual_trader_trades(
            ticker=ticker,
            period=period,
            model_name=model_name,
            limit=limit,
        )
    except ModelResultsError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error in /virtual-trader-trades")
        raise HTTPException(status_code=500, detail="Unexpected server error.") from exc

    return VirtualTraderTradesResponse(
        ticker=payload["ticker"],
        period=payload["period"],
        model_name=payload["model_name"],
        trade_count=payload["trade_count"],
        trade_log=[VirtualTraderTradeResponse(**to_json_safe_dict(item)) for item in payload["trade_log"]],
        monthly_contributions=[
            MonthlyContributionResponse(**to_json_safe_dict(item)) for item in payload["monthly_contributions"]
        ],
    )
