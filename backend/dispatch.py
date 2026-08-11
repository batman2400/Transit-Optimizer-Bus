"""
Dynamic headway / dispatch interval calculator for Route 100.
No graph search / A* — peak load → buses needed → clamped headway + corridor ETA.
"""
from __future__ import annotations

import math

CAPACITY_PER_BUS = 80
MIN_HEADWAY = 3
MAX_HEADWAY = 30
DWELL_MIN_PER_PAX = 0.05  # minutes of dwell per predicted passenger
PEAK_CONGESTION = 1.25  # weekday AM/PM multiplier on base travel

# Adjacent base travel times (minutes) along inbound corridor
# Panadura→Moratuwa→Mt_Lavinia→Dehiwala→Wellawatta→Bambalapitiya→Kollupitiya→Pettah
BASE_TRAVEL_MINUTES = [14, 12, 10, 12, 8, 8, 10]


def calculate_dispatch(
    predictions: list[float],
    stop_names: list[str] | None = None,
    *,
    hour: int | None = None,
    is_weekend: int = 0,
    is_public_holiday: int = 0,
) -> dict:
    """
    peak_load = max(predictions)
    buses_needed = max(1, ceil(peak_load / 80))
    headway = clamp(round(60 / buses_needed), 3, 30)
    corridor_eta = base_travel * congestion + sum(dwell_k * pred)
    """
    if not predictions:
        return {
            "peak_load": 0.0,
            "peak_stop": None,
            "buses_needed": 1,
            "headway_minutes": MAX_HEADWAY,
            "corridor_eta_minutes": float(sum(BASE_TRAVEL_MINUTES)),
            "congestion_factor": 1.0,
        }

    peak_idx = max(range(len(predictions)), key=lambda i: predictions[i])
    peak_load = float(predictions[peak_idx])
    peak_stop = (
        stop_names[peak_idx]
        if stop_names and peak_idx < len(stop_names)
        else None
    )

    if peak_load <= 0:
        buses_needed = 1
        headway = MAX_HEADWAY
    else:
        buses_needed = max(1, math.ceil(peak_load / CAPACITY_PER_BUS))
        raw_headway = round(60 / buses_needed)
        headway = max(MIN_HEADWAY, min(MAX_HEADWAY, raw_headway))

    soft_day = bool(is_weekend) or bool(is_public_holiday)
    congestion = 1.0
    if (
        hour is not None
        and not soft_day
        and (hour in (7, 8, 9) or hour in (16, 17, 18, 19))
    ):
        congestion = PEAK_CONGESTION

    dwell_total = sum(DWELL_MIN_PER_PAX * max(0.0, p) for p in predictions)
    corridor_eta = float(sum(BASE_TRAVEL_MINUTES) * congestion + dwell_total)

    return {
        "peak_load": round(peak_load, 2),
        "peak_stop": peak_stop,
        "buses_needed": buses_needed,
        "headway_minutes": headway,
        "corridor_eta_minutes": round(corridor_eta, 1),
        "congestion_factor": congestion,
    }
