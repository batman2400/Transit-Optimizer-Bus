# Transit Optimizer Bus — SLTB Route 100

Deep Learning–driven depot dashboard for **Route 100** (Panadura ↔ Pettah): predict passenger demand with a **PyTorch MLP**, then recommend **dispatch headway** (and corridor ETA) to reduce bus bunching.

**Status:** Baseline implemented and audit-fixed. **Colombo realism upgrade** (peak hours, calendar, cleaner rain, metrics, dashboard context) is the architecture of record — see [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md).

## Docs (any IDE)

- [AGENTS.md](AGENTS.md) — agent entrypoint / non-negotiables
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — schema, Colombo demand, model, API, dispatch
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) — checklist + verification (incl. A–D accuracy levers)

## Quick runbook

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

## What you get

| Layer | Behavior |
|-------|----------|
| ETL | ~800k stratified hybrid + Colombo peak/direction/stop/calendar + school rush + rain/event |
| Model | PyTorch MLP + MinMax/OneHot; MAE/RMSE metrics |
| API | `/predict`, `/predict/batch`, `/dispatch` (headway, peak stop, corridor ETA, `calendar_context`) |
| UI | Light depot board: holiday/school vacation/school rush overrides, corridor rail, demand chart, Open-Meteo for selected date |

## Accuracy levers (A–D)

| Lever | Goal |
|-------|------|
| **A** | Measure MAE/RMSE by stop/hour |
| **B** | Cleaner rain/event (Rain not only extreme spikes) |
| **C** | Weekday peaks push load over 80 → more buses / shorter headway |
| **D** | Peaks, CBD stops, visible weekend/holiday/payday |

## Non-negotiables

- PyTorch MLP only (no Random Forest / XGBoost)
- No A\* / no `routing.py` — `dispatch.py` headway calculator (capacity **80**)
- Do not commit large parquet / model / CSV artifacts (see `.gitignore`)
