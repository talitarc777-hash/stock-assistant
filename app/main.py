"""FastAPI entrypoint for the stock-assistant backend."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.api.analyze import router as analyze_router
from app.api.backtest import router as backtest_router
from app.api.dashboard import router as dashboard_router
from app.api.market_data import router as market_data_router
from app.api.paper import router as paper_router
from app.core.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


class HealthResponse(BaseModel):
    """Typed response for the health endpoint."""

    status: str
    app_name: str
    environment: str


settings = get_settings()

# Create the API app instance.
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Decision-support backend for stock and ETF analysis. "
        "This service gives suggestions, not automated trades."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://stock-assistant-three.vercel.app",
    ],
    # Vercel preview URLs often change per deploy; allow this project pattern too.
    allow_origin_regex=r"^https://stock-assistant-.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(market_data_router)
app.include_router(analyze_router)
app.include_router(backtest_router)
app.include_router(dashboard_router)
app.include_router(paper_router)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health_check() -> HealthResponse:
    """
    Quick endpoint to confirm the API is alive.

    Useful for smoke checks from local scripts, dashboards, or monitors.
    """
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.app_env,
    )
