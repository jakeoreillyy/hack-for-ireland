"""HTTP routes. Kept thin: validate, delegate to the service layer, return."""

from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, Request

from planning_predictor.config import Settings
from planning_predictor.schemas import PredictRequest, PredictResponse
from planning_predictor.services import prediction

router = APIRouter()


def get_applications(request: Request) -> pd.DataFrame:
    return request.app.state.applications


def get_app_settings(request: Request) -> Settings:
    """The settings the app was built with (create_app), not a fresh read of the environment."""
    return request.app.state.settings


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/predict")
def predict(
    body: PredictRequest,
    applications: Annotated[pd.DataFrame, Depends(get_applications)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> PredictResponse:
    # Sync on purpose: pandas work is CPU-bound, so FastAPI runs it in a worker thread.
    return prediction.predict(body, applications, settings)
