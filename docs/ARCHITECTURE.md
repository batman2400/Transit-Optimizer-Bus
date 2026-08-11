# Architecture — SLTB Route 100 Transit Optimizer

## Status

Implemented under `backend/` and `frontend/`. Audit mismatches (ETL columns, MinMaxScaler, headway extras, frontend DOW) have been fixed. Retrain after any ETL change.

## Problem

Bus bunching on Galle Road: a lead bus dwells long at crowded stops; following buses catch up. The system predicts crowds before departure and recommends **when to dispatch the next bus** (headway), not an alternate route.

## Pipeline

```text
public_transport.parquet
    → backend/process_hybrid_dataset.py   (~800k stratified)
    → backend/route100_final_dataset.csv
    → backend/train_model.py              (PyTorch MLP + MinMax)
    → demand_predictor.pth + preprocessor.pkl
    → backend/main.py                     (FastAPI + calendar enrich)
    → frontend/                           (Next.js + Open-Meteo)
```

## Dataset schema (`route100_final_dataset.csv`)

| Column | Type | Logic |
|--------|------|--------|
| `date` | str YYYY-MM-DD | From parquet `operating_day` (`%d.%m.%y %H:%M:%S`, dayfirst fallback) |
| `hour` | int 0–23 | `(trip_departure // 3600) % 24` |
| `direction` | categorical | Min `trip_direction` → `Inbound_to_Pettah`; else `Outbound_to_Panadura` |
| `stop_name` | categorical | `stop_id % 8` → 8 hubs below |
| `day_of_week` | int 0–6 | Mon=0 … Sun=6 (pandas `dayofweek`) |
| `is_weekend` | 0/1 | `day_of_week >= 5` |
| `is_public_holiday` | 0/1 | Sri Lanka public holidays (`holidays` LK for years in sample) |
| `is_school_holiday` | 0/1 | Month in {4, 8, 12} |
| `is_payday_week` | 0/1 | Day of month >= 25 or <= 5 |
| `event_override` | 0/1 | ~5% rows forced to 1 with demand boost |
| `weather` | Clear / Rain | Rain on 40% of top-quartile demand rows |
| `passenger_count` | int | From `passengers` (+ event multiplier) |

### Hubs

`Panadura`, `Moratuwa`, `Mt_Lavinia`, `Dehiwala`, `Wellawatta`, `Bambalapitiya`, `Kollupitiya`, `Pettah`

### ETL steps (order)

1. Stratified sample ~800k by `(trip_direction, hour)`, `seed=42`
2. Map hubs: `stop_id % 8`
3. Calendar/time from `operating_day` + `trip_departure`
4. Event injection: ~5% → `event_override=1`, `passenger_count *= Uniform(1.8, 2.5)`
5. Rain injection: among top 25% by `passenger_count`, 40% → `Rain`

**Last verified rates:** event ≈ 0.050, rain-in-top-quartile ≈ 0.400, holiday ≈ 0.071

## Neural network

- Framework: **PyTorch only**
- Preprocess: OneHot(`direction`, `weather`, `stop_name`) + **MinMaxScaler** on numeric/binary flags
- Fit preprocessor on **train split only** (80/20), then transform val
- Architecture: Input(19) → 128 + BN + ReLU + Dropout(0.2) → 64 + BN + ReLU + Dropout(0.2) → 32 ReLU → Linear(1)
- Loss: Huber; Optimizer: Adam `lr=0.001`; Early stopping patience 10; batch 512
- Artifacts:
  - `backend/models/preprocessor.pkl`
  - `backend/models/demand_predictor.pth` → `{"state_dict", "input_dim"}`

## Dispatch (no A*)

`backend/dispatch.py`:

```text
CAPACITY = 80
peak_load = max(predictions)
peak_stop = stop_names[argmax(predictions)]
buses_needed = max(1, ceil(peak_load / 80))   # or 1 if peak <= 0
headway_minutes = clamp(round(60 / buses_needed), 3, 30)
corridor_eta_minutes = sum([14,12,10,12,8,8,10]) + sum(0.05 * pred)
```

## API (`backend/main.py`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Health + model metadata (`input_dim`, stops, capacity, endpoints) |
| POST | `/predict` | Single-stop demand |
| POST | `/predict/batch` | Multi-stop demand |
| POST | `/dispatch` | 8-stop predict + headway / peak_stop / corridor ETA |

**Inference calendar enrich:** `enrich_calendar()` recomputes `day_of_week` (Mon=0), `is_weekend`, `is_public_holiday` (LK), `is_school_holiday`, `is_payday_week` from `date` so the UI cannot skew features.

**Removed:** `/route`, `routing.py`, A* Search.

## Frontend (`frontend/`)

- Next.js App Router, TypeScript, Tailwind
- Controls: date, hour, direction, weather, Event Override
- Open-Meteo Colombo (`6.9271, 79.8612`) sets default Clear/Rain on load
- Weekday helper: JS `getDay()` → Python Mon=0 via `(getDay() + 6) % 7`
- Calls `POST /dispatch`; chart from returned `stops` / `predictions`
- KPIs: headway, buses/hr, peak load + peak stop, corridor ETA

## Out of scope

- Live bus GPS / AVL
- Tree-based models
- Committing large parquet / model / CSV binaries
