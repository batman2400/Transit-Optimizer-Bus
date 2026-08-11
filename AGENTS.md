# AGENTS.md — SLTB Route 100 Transit Optimizer

Read this file first in any IDE/agent session. Full detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md).

## Status

**Implemented + audit-fixed; Colombo realism upgrade complete** (peak/calendar/rain cleanup, metrics, `calendar_context`). Folders: lowercase `backend/` and `frontend/`. Retrain after any ETL change.

## Product

Depot-manager tool for **SLTB Route 100** (Panadura ↔ Pettah via Galle Road). Predicts stop-level passenger demand with a PyTorch MLP, then recommends **dispatch headway** (plus corridor ETA) to reduce bus bunching. Not live GPS/AVL — predictive planning snapshot calibrated to **Colombo Galle Road** commute patterns (weekday AM/PM peaks, direction asymmetry, CBD hubs, LK calendar).

## Locked decisions (do not reopen)

| Decision | Value |
|----------|--------|
| ML | **PyTorch MLP only** (128+BN+Drop0.2 → 64+BN+Drop0.2 → 32 → Linear1). Huber, Adam 0.001, early stopping. No RF / XGBoost. |
| Preprocess | OneHot + **MinMaxScaler**; fit on **train split only** (prefer **time-based** 80/20 by `date`) |
| Artifacts | `backend/models/demand_predictor.pth` (state_dict + input_dim) + `preprocessor.pkl` + `metrics.json` |
| Dispatch | **Dynamic headway** — no A\*, no `routing.py`, no `/route` |
| Capacity | **80** pax/bus |
| Headway | `peak=max(8)`; `buses=max(1,ceil(peak/80))`; `headway=clamp(round(60/buses),3,30)` |
| Extra outputs | `peak_stop`, `corridor_eta_minutes` (base travel × peak congestion + 0.05×pred dwell), `calendar_context` |
| ETL | ~**800k** stratified by `(trip_direction, hour)`; `operating_day`; `trip_departure`; `stop_id % 8` |
| Colombo demand | After calendar flags, before event/rain: peak hour + direction + stop weights + calendar + **school rush ×1.40** (hours 6–7 & 13–14 on term weekdays); weekday rush peaks often **>80** so headway responds |
| Holidays | Real LK via `holidays`; **API auto-enriches from `date`**, then honors explicit `holiday_mode` / `school_holiday_mode` / `school_rush_mode` overrides; UI shows chips from `calendar_context` |
| Rain | Top 25% demand → 40% of those `weather=Rain` (`seed=42`); plus mild independent rain on ~8% non–top-quartile rows (×1.12–1.18) so Rain ≠ only extremes |
| Event | ~5% rows: `event_override=1`, demand × Uniform(1.8, 2.5) |
| Extra features | `is_am_peak` (07–09), `is_pm_peak` (16–19), `is_school_rush` (06–07 & 13–14 term weekdays), `month` (1–12) — MinMax with other numerics |
| Frontend | Light depot board (Fraunces + Manrope); Open-Meteo Colombo for **selected date**; holiday/school vacation/school rush overrides; corridor rail + KPIs + peak badge |
| Large files | Gitignore parquet, CSV, model binaries |

## Accuracy levers (A–D — in scope)

| Lever | Meaning |
|-------|---------|
| **A** | Report MAE / RMSE / R² (overall + by stop/hour/calendar/weather) → `metrics.json` |
| **B** | Cleaner rain/event: keep locked rates; Rain not only “already insane” demand |
| **C** | Responsive headway/KPIs via weekday peak loads >80 (formula unchanged) |
| **D** | Colombo realism: peaks, direction, CBD stops, visible weekend/holiday/payday |

## Key files

| Path | Role |
|------|------|
| `backend/process_hybrid_dataset.py` | Hybrid ETL + Colombo demand + rain/event |
| `backend/train_model.py` | MLP training + metrics |
| `backend/dispatch.py` | Headway + corridor ETA (+ peak congestion) |
| `backend/main.py` | FastAPI + `enrich_calendar` + `calendar_context` |
| `frontend/src/app/page.tsx` | Depot dashboard |

## Do not

- Use tree-based models
- Implement A\* or `/route`
- Commit `*.parquet`, `route100_final_dataset.csv`, or large `models/*` binaries
- Leave `event_override` always 0 in training data
- Use `StandardScaler` (must be MinMax)
- Trust raw UI-sent `is_*` calendar flags (DOW/weekend/holiday/school/rush) — API auto-enriches from `date`, then honors only explicit `holiday_mode` / `school_holiday_mode` / `school_rush_mode`
- Soften weekday peaks so corridor max stays under 80 (breaks practical headway)

## Stops (inbound order)

`Panadura` → `Moratuwa` → `Mt_Lavinia` → `Dehiwala` → `Wellawatta` → `Bambalapitiya` → `Kollupitiya` → `Pettah`
