# Transit Optimizer Bus — SLTB Route 100

Deep Learning–driven depot dashboard for **Route 100** (Panadura ↔ Pettah): predict passenger demand with a **PyTorch MLP**, then recommend **dispatch headway** (and corridor ETA) to reduce bus bunching.

**Status:** Implemented and audit-fixed. See [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md).

## Docs (any IDE)

- [AGENTS.md](AGENTS.md) — agent entrypoint / non-negotiables
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — schema, model, API, dispatch
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) — checklist + verification

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
| ETL | ~800k stratified hybrid dataset + rain/event domain injection |
| Model | PyTorch MLP + MinMax/OneHot preprocessor |
| API | `/predict`, `/predict/batch`, `/dispatch` (headway, peak stop, corridor ETA) |
| UI | Depot controls, demand chart, Open-Meteo Colombo weather default |

## Non-negotiables

- PyTorch MLP only (no Random Forest / XGBoost)
- No A\* / no `routing.py` — `dispatch.py` headway calculator (capacity **80**)
- Do not commit large parquet / model / CSV artifacts (see `.gitignore`)
