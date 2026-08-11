# Architecture — SLTB Route 100 Transit Optimizer

## Status

Implemented under `backend/` and `frontend/`. Audit mismatches fixed. **Colombo realism upgrade complete** (peak/direction/stop/calendar demand, cleaner rain, metrics, `calendar_context`) — retrain after any ETL change.

## Problem

Bus bunching on Galle Road: a lead bus dwells long at crowded stops; following buses catch up. The system predicts crowds before departure and recommends **when to dispatch the next bus** (headway), not an alternate route.

## Pipeline

```text
public_transport.parquet
    → backend/process_hybrid_dataset.py   (~800k stratified + Colombo calibration)
    → backend/route100_final_dataset.csv
    → backend/train_model.py              (PyTorch MLP + MinMax + metrics)
    → demand_predictor.pth + preprocessor.pkl + metrics.json
    → backend/main.py                     (FastAPI + calendar enrich + calendar_context)
    → frontend/                           (Next.js + Open-Meteo + calendar/peak chips)
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
| `is_am_peak` | 0/1 | Hour in {7, 8, 9} |
| `is_pm_peak` | 0/1 | Hour in {16, 17, 18, 19} |
| `is_school_rush` | 0/1 | Hour in {6, 7, 13, 14} on term weekdays (not weekend / public holiday / school holiday) |
| `month` | int 1–12 | From `date` |
| `event_override` | 0/1 | ~5% rows forced to 1 with demand boost |
| `weather` | Clear / Rain | Locked top-quartile rain + mild independent rain (see ETL) |
| `passenger_count` | int | Base passengers × Colombo multipliers (+ event / mild rain) |

### Hubs

`Panadura`, `Moratuwa`, `Mt_Lavinia`, `Dehiwala`, `Wellawatta`, `Bambalapitiya`, `Kollupitiya`, `Pettah`

### Colombo domain demand (research-backed)

Galle Road is among Colombo’s busiest corridors; morning peak often ~07:15–08:15 with strong **directional** flow into the CBD; peak load factors often >1.5. ETL teaches this via multipliers (after calendar flags, **before** event/rain):

**Peak period**

| Period | Hours | Weekday | Weekend / public holiday |
|--------|-------|---------|---------------------------|
| AM peak | 07–09 | ×2.4 | ×1.15 |
| Midday | 10–15 | ×1.1 | ×1.05 |
| PM peak | 16–19 | ×2.2 | ×1.15 |
| Off-peak | else | ×0.55 | ×0.50 |

**Direction:** Inbound ×1.35 AM / ×0.85 PM; Outbound opposite.

**Stop weights:** outer hubs ~0.85–0.95; mid ~1.0; Bambalapitiya/Kollupitiya ~1.15–1.25; Pettah ~1.3.

**Calendar stack:** payday ×1.20; public holiday ×0.70; weekend (if not holiday) ×0.80; school holiday ×0.90.

**School rush:** after the peak/direction/stop/calendar stack, term-weekday rows with `hour in {6, 7, 13, 14}` get **×1.40** (`is_school_rush=1`) to capture sudden start/finish student demand.

**Global scale:** weekday AM inbound CBD peaks commonly land in **80–200** pax so `ceil(peak/80)` yields 2+ buses and headway &lt; 30.

### ETL steps (order)

1. Stratified sample ~800k by `(trip_direction, hour)`, `seed=42`
2. Map hubs: `stop_id % 8`
3. Calendar/time from `operating_day` + `trip_departure`; set `is_am_peak` / `is_pm_peak` / `is_school_rush` / `month`
4. **Colombo demand multipliers** (peak × direction × stop × calendar × school rush × global scale)
5. Event injection: ~5% → `event_override=1`, `passenger_count *= Uniform(1.8, 2.5)`
6. Rain injection (cleaner, rates preserved):
   - Among top 25% by `passenger_count`, 40% → `Rain` (locked)
   - Additionally ~8% of non–top-quartile, non-event rows → `Rain` with mild uplift ×1.12–1.18

**Target rates:** event ≈ 0.050, rain-in-top-quartile ≈ 0.400; Clear weekday peaks already high so Rain is a bump, not the only path to high demand.

## Neural network

- Framework: **PyTorch only**
- Preprocess: OneHot(`direction`, `weather`, `stop_name`) + **MinMaxScaler** on numeric/binary flags including `is_am_peak`, `is_pm_peak`, `is_school_rush`, `month`
- Fit preprocessor on **train only**; prefer **time-based** 80/20 by `date`
- Architecture: Input(dim) → 128 + BN + ReLU + Dropout(0.2) → 64 + BN + ReLU + Dropout(0.2) → 32 ReLU → Linear(1)
- Loss: Huber; Optimizer: Adam `lr=0.001`; Early stopping patience 10; batch 512
- Eval: MAE / RMSE / R² overall + by hour / stop / calendar / weather → `models/metrics.json`
- Artifacts:
  - `backend/models/preprocessor.pkl`
  - `backend/models/demand_predictor.pth` → `{"state_dict", "input_dim"}`
  - `backend/models/metrics.json`

## Dispatch (no A*)

`backend/dispatch.py`:

```text
CAPACITY = 80
peak_load = max(predictions)
peak_stop = stop_names[argmax(predictions)]
buses_needed = max(1, ceil(peak_load / 80))   # or 1 if peak <= 0
headway_minutes = clamp(round(60 / buses_needed), 3, 30)
base_travel = sum([14,12,10,12,8,8,10])
# weekday AM/PM peak: multiply base_travel by ~1.25 (congestion); else 1.0
corridor_eta_minutes = base_travel * congestion + sum(0.05 * pred)
```

Headway formula is unchanged; peak congestion only affects ETA.

## API (`backend/main.py`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Health + model metadata (`input_dim`, stops, capacity, endpoints) |
| POST | `/predict` | Single-stop demand |
| POST | `/predict/batch` | Multi-stop demand |
| POST | `/dispatch` | 8-stop predict + headway / peak_stop / corridor ETA + `calendar_context` |

**Inference calendar enrich:** `enrich_calendar()` always auto-computes `day_of_week` (Mon=0), `is_weekend`, LK `is_public_holiday`, `is_school_holiday` (Apr/Aug/Dec), `is_payday_week`, plus `is_am_peak` / `is_pm_peak` / `month` from `date`+`hour`, then `is_school_rush` from hour + applied soft-day/school flags. Raw client `is_*` fields are ignored. Explicit overrides (after auto):

| Field | Values | Effect |
|-------|--------|--------|
| `holiday_mode` | `auto` (default), `none`, `poya`, `government` | Forces `is_public_holiday` (Poya and Government both → 1; display type differs) |
| `school_holiday_mode` | `auto` (default), `off`, `on` | Forces `is_school_holiday` |
| `school_rush_mode` | `auto` (default), `off`, `on` | Forces `is_school_rush` |

Auto public holidays are classified for display: name contains `"Poya"` → `poya`, else `government`.

**`calendar_context` on `/dispatch`:**

```json
{
  "date": "YYYY-MM-DD",
  "day_of_week": 0,
  "day_name": "Monday",
  "is_weekend": 0,
  "is_public_holiday": 0,
  "public_holiday_name": null,
  "is_school_holiday": 0,
  "is_school_rush": 0,
  "is_payday_week": 1,
  "peak_period": "am_peak",
  "holiday_type": "none",
  "holiday_mode": "auto",
  "school_holiday_mode": "auto",
  "school_rush_mode": "auto",
  "auto_holiday_type": "none",
  "auto_is_school_holiday": 0,
  "auto_is_school_rush": 0,
  "auto_public_holiday_name": null,
  "override_active": false
}
```

`peak_period`: `am_peak` | `midday` | `pm_peak` | `off_peak`.  
`holiday_type` / `auto_holiday_type`: `none` | `poya` | `government`.

**Removed:** `/route`, `routing.py`, A* Search.

## Frontend (`frontend/`)

- Next.js App Router, TypeScript, Tailwind — light **depot board** (Fraunces + Manrope; teal/ink palette)
- Controls: date, hour, direction, weather, Event Override, **day type** (`holiday_mode`), **school vacation** (`school_holiday_mode`), **school rush** (`school_rush_mode`)
- Open-Meteo Colombo (`6.9271, 79.8612`) for **selected date** (forecast/archive)
- Context strip from `calendar_context` (weekday, weekend, holiday type + name, school vacation, school rush, payday)
- Auto-detect hints when modes are `auto`; “Override active” when moderator overrides
- Corridor stop rail with peak-stop highlight; demand bar chart; KPI readout (headway, buses/hr, peak load, corridor ETA)
- Calls `POST /dispatch` with `holiday_mode` + `school_holiday_mode` + `school_rush_mode` (does not send raw `is_*` flags)

## Accuracy levers (A–D)

| Lever | Behavior |
|-------|----------|
| A | Train reports MAE/RMSE/R² (+ breakdowns) → `metrics.json` |
| B | Rain: locked top-quartile labeling + mild independent rain |
| C | Weekday peaks often >80 → more buses / shorter headway |
| D | Peaks, direction, CBD stops, visible calendar |

## Out of scope

- Live bus GPS / AVL / true SLTB smart-card Route 100 counts
- Tree-based models
- Changing capacity or headway clamp formula
- Replacing `stop_id % 8` with real stop IDs (needs new source data)
- Committing large parquet / model / CSV binaries
