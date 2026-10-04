"""Application factory. Run with: uvicorn planning_predictor.main:app --reload"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from planning_predictor.api.routes import router
from planning_predictor.config import Settings, get_settings
from planning_predictor.repository import load_applications


def create_app(
    settings: Settings | None = None, applications: pd.DataFrame | None = None
) -> FastAPI:
    """Build the app. Pass `settings` or `applications` to skip reading them from disk (tests)."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.applications = (
            applications if applications is not None else load_applications(settings.data_dir)
        )
        yield

    app = FastAPI(title="Planning permission predictor", lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
