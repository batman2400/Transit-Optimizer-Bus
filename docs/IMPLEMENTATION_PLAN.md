# Implementation Plan — SLTB Route 100

**Status: complete.** Architecture locked, code shipped, audit fixes applied, ETL + MLP retrained.

**Source of truth:** this file + [ARCHITECTURE.md](ARCHITECTURE.md) + [/AGENTS.md](../AGENTS.md).  
On-disk paths: `backend/`, `frontend/` (lowercase).

## Locked answers (closed)

1. Neural net required → **PyTorch MLP only** (no RF/XGBoost)
2. Event override training → **~5%**, demand × Uniform(1.8, 2.5)
3. A\* required → **No**; dynamic headway only
4. Capacity → **80**; headway = clamp(round(60 / max(1, ceil(peak/80))), 3, 30)
5. Frontend weather → **Open-Meteo Colombo**
6. ETL → **~800k stratified** by (direction, hour); `operating_day` + `trip_departure` + `stop_id % 8`
7. Holidays → **LK via `holidays`**; API `enrich_calendar` at inference
8. Scaler → **MinMaxScaler** (not StandardScaler)
9. Git → gitignore parquet / models / CSV

## Checklist

### Documentation & rules

- [x] `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/IMPLEMENTATION_PLAN.md`
- [x] `.cursor/rules/sltb-route100.mdc`
- [x] `.gitignore` large artifacts (`backend/` + `Backend/` patterns)
- [x] `README.md` runbook

### Backend

- [x] `backend/requirements.txt` (incl. `joblib`, `holidays`, `torch`, …)
- [x] `backend/process_hybrid_dataset.py` — stratified ETL + rain/event injection
- [x] `backend/train_model.py` — MinMax + MLP + early stopping
- [x] `backend/dispatch.py` — headway, peak_stop, corridor_eta
- [x] `backend/main.py` — `/`, `/predict`, `/predict/batch`, `/dispatch` + calendar enrich
- [x] No `routing.py` / no `/route`

### Frontend

- [x] Next.js App Router + Tailwind + TS under `frontend/`
- [x] Controls + Open-Meteo default weather
- [x] Demand bar chart + dispatch KPIs (headway, buses, peak load/stop, corridor ETA)
- [x] Mon=0 day-of-week encoding; layout metadata titled for Route 100

### Audit fixes (applied)

- [x] ETL: stratified sample (not plain random)
- [x] ETL: `operating_day` / `trip_departure` / `stop_id % 8` (not synthetic dates / enumerate map)
- [x] Train: MinMaxScaler; preprocessor fit on train only
- [x] Dispatch: corridor ETA + peak_stop; `buses_needed >= 1`
- [x] API: `GET /` metadata; lifespan load; calendar enrich
- [x] Frontend: DOW/weekend fix; corridor ETA + peak stop UI
- [x] Docs path casing (`backend/` / `frontend/`)

## Verification (last run)

| Check | Result |
|-------|--------|
| ETL rows | 800,000 |
| event_rate | 0.050 |
| rain_in_top_quartile | 0.400 |
| holiday_rate | ~0.071 |
| Preprocessor | MinMaxScaler confirmed |
| MLP checkpoint | `input_dim=19`, early stop ~epoch 14 |
| Dispatch sample | returns `peak_stop`, `corridor_eta_minutes`, headway in [3, 30] |

## Runbook

```text
cd backend
pip install -r requirements.txt
python process_hybrid_dataset.py
python train_model.py
uvicorn main:app --reload --port 8000

cd ../frontend
npm install
npm run dev
```
