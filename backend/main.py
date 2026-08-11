"""
FastAPI service: demand prediction + dynamic headway dispatch for Route 100.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import List

import holidays
import joblib
import numpy as np
import pandas as pd
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dispatch import calculate_dispatch
from train_model import DemandPredictorMLP

STOPS_INBOUND = [
    "Panadura",
    "Moratuwa",
    "Mt_Lavinia",
    "Dehiwala",
    "Wellawatta",
    "Bambalapitiya",
    "Kollupitiya",
    "Pettah",
]

model = None
preprocessor = None
input_dim = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _load_artifacts() -> None:
    global model, preprocessor, input_dim
    preprocessor = joblib.load("models/preprocessor.pkl")
    checkpoint = torch.load(
        "models/demand_predictor.pth", map_location=device, weights_only=False
    )
    if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        input_dim = int(checkpoint["input_dim"])
        state = checkpoint["state_dict"]
    else:
        # Backward-compat: raw state_dict
        dummy_df = pd.DataFrame(
            [
                {
                    "direction": "Inbound_to_Pettah",
                    "stop_name": "Panadura",
                    "weather": "Clear",
                    "hour": 8,
                    "day_of_week": 0,
                    "is_weekend": 0,
                    "is_public_holiday": 0,
                    "is_school_holiday": 0,
                    "is_payday_week": 0,
                    "event_override": 0,
                }
            ]
        )
        input_dim = preprocessor.transform(dummy_df).shape[1]
        state = checkpoint

    model = DemandPredictorMLP(input_dim)
    model.load_state_dict(state)
    model.to(device)
    model.eval()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        _load_artifacts()
        print("Model and preprocessor loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        raise
    yield


app = FastAPI(
    title="Route 100 Transit Optimizer API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictionRequest(BaseModel):
    date: str
    hour: int
    direction: str
    stop_name: str
    day_of_week: int | None = None
    is_weekend: int | None = None
    is_public_holiday: int | None = None
    is_school_holiday: int | None = None
    is_payday_week: int | None = None
    event_override: int = 0
    weather: str = "Clear"


class BatchPredictionRequest(BaseModel):
    requests: List[PredictionRequest]


class DispatchRequest(BaseModel):
    date: str
    hour: int
    direction: str
    day_of_week: int | None = None
    is_weekend: int | None = None
    is_public_holiday: int | None = None
    is_school_holiday: int | None = None
    is_payday_week: int | None = None
    event_override: int = 0
    weather: str = "Clear"


def enrich_calendar(row: dict) -> dict:
    """Recompute calendar flags from date (Mon=0) so UI encoding bugs cannot skew inference."""
    d = pd.to_datetime(row["date"], errors="coerce")
    if pd.isna(d):
        raise HTTPException(status_code=400, detail=f"Invalid date: {row.get('date')}")
    out = dict(row)
    out["day_of_week"] = int(d.dayofweek)
    out["is_weekend"] = 1 if d.dayofweek >= 5 else 0
    lk = holidays.country_holidays("LK", years=[int(d.year)])
    out["is_public_holiday"] = 1 if d.date() in lk else 0
    out["is_school_holiday"] = 1 if d.month in (4, 8, 12) else 0
    out["is_payday_week"] = 1 if (d.day >= 25 or d.day <= 5) else 0
    return out


def _ensure_ready() -> None:
    if model is None or preprocessor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")


def process_and_predict(data: List[dict]) -> List[float]:
    _ensure_ready()
    if not data:
        return []
    enriched = [enrich_calendar(row) for row in data]
    df = pd.DataFrame(enriched)
    feature_cols = [
        "direction",
        "stop_name",
        "weather",
        "hour",
        "day_of_week",
        "is_weekend",
        "is_public_holiday",
        "is_school_holiday",
        "is_payday_week",
        "event_override",
    ]
    try:
        X_processed = preprocessor.transform(df[feature_cols]).astype(np.float32)
        X_tensor = torch.tensor(X_processed).to(device)
        with torch.no_grad():
            predictions = model(X_tensor).cpu().numpy().flatten()
        return [float(p) for p in predictions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/")
def read_root():
    return {
        "status": "ok",
        "service": "Route 100 Transit Optimizer",
        "framework": "PyTorch MLP",
        "input_dim": input_dim,
        "model_loaded": model is not None,
        "preprocessor_loaded": preprocessor is not None,
        "stops": STOPS_INBOUND,
        "endpoints": ["/", "/predict", "/predict/batch", "/dispatch"],
        "capacity_per_bus": 80,
    }


@app.post("/predict")
def predict(request: PredictionRequest):
    data = [request.model_dump()]
    preds = process_and_predict(data)
    return {"passenger_count": max(0, preds[0])}


@app.post("/predict/batch")
def predict_batch(request: BatchPredictionRequest):
    data = [req.model_dump() for req in request.requests]
    preds = process_and_predict(data)
    return {"predictions": [max(0, p) for p in preds]}


@app.post("/dispatch")
def dispatch(request: DispatchRequest):
    stops = (
        STOPS_INBOUND
        if request.direction == "Inbound_to_Pettah"
        else list(reversed(STOPS_INBOUND))
    )
    req_dict = request.model_dump()
    data = []
    for stop in stops:
        row = req_dict.copy()
        row["stop_name"] = stop
        data.append(row)

    preds = [max(0, p) for p in process_and_predict(data)]
    dispatch_info = calculate_dispatch(preds, stops)

    return {
        "stops": stops,
        "predictions": preds,
        "dispatch_recommendation": dispatch_info,
    }
