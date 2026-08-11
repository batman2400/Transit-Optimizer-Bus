# Implementation Plan — SLTB Route 100

**Status: Colombo realism upgrade complete.** Architecture locked (MLP, headway, no A*). Source of truth: this file + [ARCHITECTURE.md](ARCHITECTURE.md) + [/AGENTS.md](../AGENTS.md).  
On-disk paths: `backend/`, `frontend/` (lowercase).

## Locked answers (closed)

1. Neural net required → **PyTorch MLP only** (no RF/XGBoost)
2. Event override training → **~5%**, demand × Uniform(1.8, 2.5)
3. A\* required → **No**; dynamic headway only
4. Capacity → **80**; headway = clamp(round(60 / max(1, ceil(peak/80))), 3, 30)
5. Frontend weather → **Open-Meteo Colombo** (selected date)
6. ETL → **~800k stratified** by (direction, hour); `operating_day` + `trip_departure` + `stop_id % 8`
7. Holidays → **LK via `holidays`**; API auto-enrich + optional `holiday_mode` / `school_holiday_mode` / `school_rush_mode`; UI shows `calendar_context`
8. Scaler → **MinMaxScaler** (not StandardScaler)
9. Git → gitignore parquet / models / CSV
10. Colombo demand → peak/direction/stop/calendar + school-rush ×1.40 (06–07 & 13–14 term weekdays); weekday rush peaks often >80
11. Rain → top-quartile 40% Rain **plus** mild independent rain (~8% non–top-quartile ×1.12–1.18)
12. Extra features → `is_am_peak`, `is_pm_peak`, `is_school_rush`, `month`; metrics → `models/metrics.json`

## Accuracy levers (A–D)

| Lever | Status |
|-------|--------|
| **A** Measure MAE/RMSE by stop/hour (+ calendar/weather) | [x] `train_model.py` → `metrics.json` |
| **B** Cleaner rain/event (less fake “Rain = only extremes”) | [x] ETL rain cleanup |
| **C** Responsive headway via peak loads >80 (formula locked) | [x] Colombo peak scale |
| **D** Peaks / flat stops / missing calendar | [x] ETL profile + API/UI chips |

## Checklist

### Documentation & rules

- [x] `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/IMPLEMENTATION_PLAN.md`
- [x] `.cursor/rules/sltb-route100.mdc`
- [x] `.gitignore` large artifacts (`backend/` + `Backend/` patterns)
- [x] `README.md` runbook
- [x] Docs updated for Colombo realism + A–D levers

### Backend (baseline — done)

- [x] `backend/requirements.txt` (incl. `joblib`, `holidays`, `torch`, …)
- [x] `backend/process_hybrid_dataset.py` — stratified ETL + rain/event injection
- [x] `backend/train_model.py` — MinMax + MLP + early stopping
- [x] `backend/dispatch.py` — headway, peak_stop, corridor_eta
- [x] `backend/main.py` — `/`, `/predict`, `/predict/batch`, `/dispatch` + calendar enrich
- [x] No `routing.py` / no `/route`

### Colombo realism upgrade

- [x] ETL: peak hour + direction + stop weights + calendar multipliers + global scale
- [x] ETL: `is_am_peak` / `is_pm_peak` / `month` columns
- [x] ETL: cleaner rain (locked top-quartile 40% + mild independent rain)
- [x] Train: time-based split; MAE/RMSE/R² + breakdowns → `metrics.json`
- [x] API: return `calendar_context` (incl. LK holiday name + `peak_period`)
- [x] API/dispatch: weekday AM/PM peak congestion bump on corridor ETA (~1.25× base travel)
- [x] Wire new features through preprocessor + `enrich_calendar` / predict path
- [x] Re-run ETL + train; verify weekday 08:00 inbound often buses ≥ 2 / headway ≤ 30

### Frontend

- [x] Next.js App Router + Tailwind + TS under `frontend/`
- [x] Controls + Open-Meteo default weather
- [x] Demand bar chart + dispatch KPIs (headway, buses, peak load/stop, corridor ETA)
- [x] Mon=0 day-of-week encoding; layout metadata titled for Route 100
- [x] Calendar chips from `calendar_context`
- [x] Peak period badge
- [x] Open-Meteo for **selected date**
- [x] KPI peak cue when buses/headway tighten
- [x] Full depot-board UI redesign (light teal/ink; Fraunces + Manrope; corridor rail)
- [x] Moderator holiday override: day type Auto/Working/Poya/Government + school vacation Auto/No/Yes
- [x] Payload sends `holiday_mode` / `school_holiday_mode` / `school_rush_mode`; context shows suggestion vs applied

### API holiday override

- [x] `holiday_mode`: auto | none | poya | government
- [x] `school_holiday_mode`: auto | off | on
- [x] `school_rush_mode`: auto | off | on
- [x] Expanded `calendar_context` (holiday_type, auto_*, is_school_rush, override_active)

### School time crowd

- [x] ETL: `is_school_rush` on term weekdays hours {6,7,13,14} with ×1.40 demand bump
- [x] Train: feature + `by_school_rush` metrics; retrain → `input_dim=23`
- [x] API enrich + `school_rush_mode` override
- [x] UI School rush Auto/No/Yes + context chip

### Audit fixes (applied)

- [x] ETL: stratified sample (not plain random)
- [x] ETL: `operating_day` / `trip_departure` / `stop_id % 8` (not synthetic dates / enumerate map)
- [x] Train: MinMaxScaler; preprocessor fit on train only
- [x] Dispatch: corridor ETA + peak_stop; `buses_needed >= 1`
- [x] API: `GET /` metadata; lifespan load; calendar enrich
- [x] Frontend: DOW/weekend fix; corridor ETA + peak stop UI
- [x] Docs path casing (`backend/` / `frontend/`)

## Verification

### Baseline (prior)

| Check | Result |
|-------|--------|
| ETL rows | 800,000 |
| event_rate | 0.050 |
| rain_in_top_quartile | 0.400 |
| holiday_rate | ~0.071 |
| Preprocessor | MinMaxScaler confirmed |
| MLP checkpoint | `input_dim=19`, early stop ~epoch 14 |
| Dispatch sample | returns `peak_stop`, `corridor_eta_minutes`, headway in [3, 30] |

### After Colombo upgrade + school rush (latest run)

| Check | Result |
|-------|--------|
| ETL rows | 800,000 |
| event_rate | 0.050 |
| rain_in_top_quartile | 0.406 |
| holiday_rate | 0.071 |
| school_rush_rate | ~0.139 |
| weekday_08 inbound CBD p90 (labels) | high (peaks >80) |
| MLP | `input_dim=23`, early stop ~epoch 31, best @ 21 |
| metrics.json | MAE / RMSE / R² + by hour/stop/calendar/weather/school_rush |
| Weekday 07:00 term rush on vs off | peak higher with `school_rush_mode=on` |
| `/dispatch` | returns `calendar_context` incl. `is_school_rush` |

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

API docs: http://127.0.0.1:8000/docs · Dashboard: http://localhost:3000
