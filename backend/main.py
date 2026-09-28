"""
FastAPI service: demand prediction + dynamic headway dispatch for Route 100.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import List, Literal

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

HolidayMode = Literal["auto", "none", "poya", "government"]
SchoolHolidayMode = Literal["auto", "off", "on"]
SchoolRushMode = Literal["auto", "off", "on"]
HolidayType = Literal["none", "poya", "government"]
SCHOOL_RUSH_HOURS = (6, 7, 13, 14)

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

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

FEATURE_COLS = [
    "direction",
    "stop_name",
    "weather",
    "hour",
    "day_of_week",
    "is_weekend",
    "is_public_holiday",
    "is_school_holiday",
    "is_payday_week",
    "is_am_peak",
    "is_pm_peak",
    "is_school_rush",
    "month",
    "event_override",
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
                    "is_am_peak": 1,
                    "is_pm_peak": 0,
                    "is_school_rush": 0,
                    "month": 1,
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
    is_am_peak: int | None = None
    is_pm_peak: int | None = None
    month: int | None = None
    event_override: int = 0
    weather: str = "Clear"
    holiday_mode: HolidayMode = "auto"
    school_holiday_mode: SchoolHolidayMode = "auto"
    school_rush_mode: SchoolRushMode = "auto"


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
    is_am_peak: int | None = None
    is_pm_peak: int | None = None
    month: int | None = None
    event_override: int = 0
    weather: str = "Clear"
    holiday_mode: HolidayMode = "auto"
    school_holiday_mode: SchoolHolidayMode = "auto"
    school_rush_mode: SchoolRushMode = "auto"


def peak_period_label(hour: int) -> str:
    if hour in (7, 8, 9):
        return "am_peak"
    if 10 <= hour <= 15:
        return "midday"
    if hour in (16, 17, 18, 19):
        return "pm_peak"
    return "off_peak"


def _normalize_holiday_mode(value: object) -> HolidayMode:
    if value in ("auto", "none", "poya", "government"):
        return value  # type: ignore[return-value]
    return "auto"


def _normalize_school_mode(value: object) -> SchoolHolidayMode:
    if value in ("auto", "off", "on"):
        return value  # type: ignore[return-value]
    return "auto"


def _normalize_school_rush_mode(value: object) -> SchoolRushMode:
    if value in ("auto", "off", "on"):
        return value  # type: ignore[return-value]
    return "auto"


def classify_holiday_type(is_public_holiday: int, holiday_name: str | None) -> HolidayType:
    if not is_public_holiday:
        return "none"
    if holiday_name and "poya" in holiday_name.lower():
        return "poya"
    return "government"


def enrich_calendar(row: dict) -> dict:
    """Auto calendar from date/hour, then honor holiday/school/rush mode overrides."""
    d = pd.to_datetime(row["date"], errors="coerce")
    if pd.isna(d):
        raise HTTPException(status_code=400, detail=f"Invalid date: {row.get('date')}")
    hour = int(row.get("hour", 0))
    out = dict(row)
    out["event_override"] = int(row.get("event_override", 0))
    out["weather"] = str(row.get("weather", "Clear"))

    # Auto baseline — ignore any client-sent is_* calendar flags.
    out["day_of_week"] = int(d.dayofweek)
    out["is_weekend"] = 1 if d.dayofweek >= 5 else 0
    lk = holidays.country_holidays("LK", years=[int(d.year)])
    auto_public = 1 if d.date() in lk else 0
    auto_school = 1 if d.month in (4, 8, 12) else 0
    auto_name = lk.get(d.date()) if auto_public else None
    auto_type = classify_holiday_type(auto_public, auto_name)

    holiday_mode = _normalize_holiday_mode(row.get("holiday_mode", "auto"))
    school_mode = _normalize_school_mode(row.get("school_holiday_mode", "auto"))
    rush_mode = _normalize_school_rush_mode(row.get("school_rush_mode", "auto"))

    if holiday_mode == "auto":
        out["is_public_holiday"] = auto_public
        holiday_type: HolidayType = auto_type
        display_name = auto_name
    elif holiday_mode == "none":
        out["is_public_holiday"] = 0
        holiday_type = "none"
        display_name = None
    elif holiday_mode == "poya":
        out["is_public_holiday"] = 1
        holiday_type = "poya"
        display_name = auto_name if auto_type == "poya" else "Poya Day (override)"
    else:  # government
        out["is_public_holiday"] = 1
        holiday_type = "government"
        display_name = (
            auto_name if auto_type == "government" else "Government holiday (override)"
        )

    if school_mode == "auto":
        out["is_school_holiday"] = auto_school
    elif school_mode == "on":
        out["is_school_holiday"] = 1
    else:
        out["is_school_holiday"] = 0

    out["is_payday_week"] = 1 if (d.day >= 25 or d.day <= 5) else 0
    out["is_am_peak"] = 1 if hour in (7, 8, 9) else 0
    out["is_pm_peak"] = 1 if hour in (16, 17, 18, 19) else 0
    out["month"] = int(d.month)

    # School rush after applied holiday/school flags (term weekday + rush hours).
    auto_rush = (
        1
        if (
            hour in SCHOOL_RUSH_HOURS
            and out["is_weekend"] == 0
            and out["is_public_holiday"] == 0
            and out["is_school_holiday"] == 0
        )
        else 0
    )
    if rush_mode == "auto":
        out["is_school_rush"] = auto_rush
    elif rush_mode == "on":
        out["is_school_rush"] = 1
    else:
        out["is_school_rush"] = 0

    # Context fields (not model features)
    out["_holiday_mode"] = holiday_mode
    out["_school_holiday_mode"] = school_mode
    out["_school_rush_mode"] = rush_mode
    out["_holiday_type"] = holiday_type
    out["_public_holiday_name"] = display_name
    out["_auto_holiday_type"] = auto_type
    out["_auto_is_school_holiday"] = auto_school
    out["_auto_is_school_rush"] = auto_rush
    out["_auto_public_holiday_name"] = auto_name
    out["_override_active"] = (
        holiday_mode != "auto"
        or school_mode != "auto"
        or rush_mode != "auto"
    )
    return out


def build_calendar_context(row: dict) -> dict:
    """Calendar payload for the depot UI (suggestion vs applied)."""
    d = pd.to_datetime(row["date"], errors="coerce")
    if pd.isna(d):
        raise HTTPException(status_code=400, detail=f"Invalid date: {row.get('date')}")
    enriched = enrich_calendar(row)
    return {
        "date": d.strftime("%Y-%m-%d"),
        "day_of_week": enriched["day_of_week"],
        "day_name": DAY_NAMES[enriched["day_of_week"]],
        "is_weekend": enriched["is_weekend"],
        "is_public_holiday": enriched["is_public_holiday"],
        "public_holiday_name": enriched["_public_holiday_name"],
        "is_school_holiday": enriched["is_school_holiday"],
        "is_school_rush": enriched["is_school_rush"],
        "is_payday_week": enriched["is_payday_week"],
        "peak_period": peak_period_label(int(row.get("hour", 0))),
        "holiday_type": enriched["_holiday_type"],
        "holiday_mode": enriched["_holiday_mode"],
        "school_holiday_mode": enriched["_school_holiday_mode"],
        "school_rush_mode": enriched["_school_rush_mode"],
        "auto_holiday_type": enriched["_auto_holiday_type"],
        "auto_is_school_holiday": enriched["_auto_is_school_holiday"],
        "auto_is_school_rush": enriched["_auto_is_school_rush"],
        "auto_public_holiday_name": enriched["_auto_public_holiday_name"],
        "override_active": enriched["_override_active"],
    }


def _ensure_ready() -> None:
    if model is None or preprocessor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")


def process_and_predict(data: List[dict]) -> List[float]:
    _ensure_ready()
    if not data:
        return []
    enriched = [enrich_calendar(row) for row in data]
    df = pd.DataFrame(enriched)
    try:
        X_processed = preprocessor.transform(df[FEATURE_COLS]).astype(np.float32)
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
    calendar_context = build_calendar_context(req_dict)
    data = []
    for stop in stops:
        row = req_dict.copy()
        row["stop_name"] = stop
        data.append(row)

    preds = [max(0, p) for p in process_and_predict(data)]
    dispatch_info = calculate_dispatch(
        preds,
        stops,
        hour=request.hour,
        is_weekend=calendar_context["is_weekend"],
        is_public_holiday=calendar_context["is_public_holiday"],
    )

    return {
        "stops": stops,
        "predictions": preds,
        "dispatch_recommendation": dispatch_info,
        "calendar_context": calendar_context,
    }
