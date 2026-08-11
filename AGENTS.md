# AGENTS.md — SLTB Route 100 Transit Optimizer

Read this file first in any IDE/agent session. Full detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md).

## Status

**Implemented and audit-fixed.** Folders on disk: lowercase `backend/` and `frontend/`.

## Product

Depot-manager tool for **SLTB Route 100** (Panadura ↔ Pettah via Galle Road). Predicts stop-level passenger demand with a PyTorch MLP, then recommends **dispatch headway** (plus corridor ETA) to reduce bus bunching. Not live GPS/AVL — predictive planning snapshot.

## Locked decisions (do not reopen)

| Decision | Value |
|----------|--------|
| ML | **PyTorch MLP only** (128+BN+Drop0.2 → 64+BN+Drop0.2 → 32 → Linear1). Huber, Adam 0.001, early stopping. No RF / XGBoost. |
| Preprocess | OneHot + **MinMaxScaler**; fit on **train split only** |
| Artifacts | `backend/models/demand_predictor.pth` (state_dict + input_dim) + `preprocessor.pkl` |
| Dispatch | **Dynamic headway** — no A\*, no `routing.py`, no `/route` |
| Capacity | **80** pax/bus |
| Headway | `peak=max(8)`; `buses=max(1,ceil(peak/80))`; `headway=clamp(round(60/buses),3,30)` |
| Extra outputs | `peak_stop`, `corridor_eta_minutes` (base travel + 0.05×pred dwell) |
| ETL | ~**800k** stratified by `(trip_direction, hour)`; `operating_day`; `trip_departure`; `stop_id % 8` |
| Holidays | Real LK via `holidays`; **API recomputes calendar flags from `date` at inference** |
| Rain | Top 25% demand → 40% of those `weather=Rain` (`seed=42`) |
| Event | ~5% rows: `event_override=1`, demand × Uniform(1.8, 2.5) |
| Frontend | Open-Meteo Colombo default; DOW encoded Mon=0; KPIs include peak stop + corridor ETA |
| Large files | Gitignore parquet, CSV, model binaries |

## Key files

| Path | Role |
|------|------|
| `backend/process_hybrid_dataset.py` | Hybrid ETL |
| `backend/train_model.py` | MLP training |
| `backend/dispatch.py` | Headway + corridor ETA |
| `backend/main.py` | FastAPI |
| `frontend/src/app/page.tsx` | Depot dashboard |

## Do not

- Use tree-based models
- Implement A\* or `/route`
- Commit `*.parquet`, `route100_final_dataset.csv`, or large `models/*` binaries
- Leave `event_override` always 0 in training data
- Use `StandardScaler` (must be MinMax)
- Trust UI-sent `day_of_week` / holiday flags without API `enrich_calendar`

## Stops (inbound order)

`Panadura` → `Moratuwa` → `Mt_Lavinia` → `Dehiwala` → `Wellawatta` → `Bambalapitiya` → `Kollupitiya` → `Pettah`
