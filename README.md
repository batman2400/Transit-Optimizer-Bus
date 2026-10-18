# AI-Powered Dynamic Public Transport Fleet Optimizer (SLTB Route 100)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/framework-PyTorch%20%7C%20FastAPI%20%7C%20Next.js-orange.svg)]()
[![Course](https://img.shields.io/badge/KDU-Essentials%20of%20AI-purple.svg)]()

Deep Learning–driven decision support system for **SLTB Route 100** (Panadura ↔ Pettah along Galle Road). Predicts stop-level passenger demand with a **PyTorch MLP**, then recommends **dynamic dispatch headways** and corridor travel times to mitigate bus bunching.

Developed for **General Sir John Kotelawala Defence University (KDU)**, Faculty of Computing — *Essentials of Artificial Intelligence* (Group 40).

---

## 👥 Group 40 Team Members

| Index Number | Name | Degree / Intake | Component & Primary Role |
| :--- | :--- | :--- | :--- |
| **D/BSE/25/0012** | **M Uvaram** | Software Engineering (BSE 42) | AI/ML Development: PyTorch MLP Architecture, Model Training & Evaluation |
| **D/DBA/25/0016** | **TTC Jayasinghe** | Data Science & Business Analytics (DBA 42) | Data Engineering: Hybrid ETL, Stratified Sampling & Colombo Domain Modeling |
| **D/BIT/24/0039** | **SNMRDS Arambepola** | Information Technology (BIT 41) | Optimization & Backend: Dynamic Headway Logic, Corridor ETA & FastAPI Services |
| **D/BIT/24/0056** | **JGJB Gamage** | Information Technology (BIT 41) | Decision Support UI: Next.js Depot Dashboard, Corridor Rail & Live Weather |

---

## 📑 Project Deliverables

- 📄 **[Final Project Report](Reports/Final%20Report%20(Group%2040).pdf)**: Complete 22-page technical report covering problem background, AI techniques, system design, testing matrix, and ethics.
- 📊 **[Final Presentation Deck](Reports/Route100_Fleet_Optimizer_Group40.pptx)**: 14-slide presentation deck.
- 📋 **[Individual Contribution Reports](Reports/individual%20contribution%20reports/)**: Individual contribution sheets with attached technical evidence for all four team members.

---

## 🚌 Corridor Overview (Route 100)

The system models the 8 key strategic passenger hubs along Galle Road (Inbound / Outbound):

```text
Panadura ⟷ Moratuwa ⟷ Mt. Lavinia ⟷ Dehiwala ⟷ Wellawatta ⟷ Bambalapitiya ⟷ Kollupitiya ⟷ Pettah
```

---

## 🧠 System Architecture & Results

1. **Hybrid Data Engineering**: ~800,000 records stratified by `(trip_direction, hour)` calibrated with Colombo commuting patterns (AM inbound rush 2.4×, PM outbound rush 2.2×, school rush 1.40×, Sri Lanka public/Poya holidays via `holidays` library, and monsoon rain shocks).
2. **PyTorch MLP Demand Predictor**:
   - 4-layer neural network ($23 \to 128 \to 64 \to 32 \to 1$) with `BatchNorm1d` and `Dropout(0.2)`.
   - Trained with **Huber loss (Smooth L1)** and Adam ($\eta = 0.001$) with early stopping.
   - Evaluated on $158,622$ chronological holdout test records:
     - **MAE**: 225.8 passengers
     - **RMSE**: 519.3 passengers
     - **$R^2$ Score**: 0.331
3. **Dynamic Dispatch Logic**:
   - $\text{peak\_load} = \max(\text{predictions})$
   - $\text{buses\_needed} = \max(1, \lceil \text{peak\_load} / 80 \rceil)$ (80 pax/bus capacity)
   - $\text{headway} = \text{clamp}(\text{round}(60 / \text{buses\_needed}), 3, 30)$ minutes
   - $\text{Corridor ETA} = (\text{Base Travel} \times \text{Congestion}) + (0.05 \text{ min/pax} \times \text{Total Load})$
4. **Interactive Dashboard**: Next.js depot master view with real-time KPI cards, interactive corridor rail, Open-Meteo Colombo live weather integration, and scenario override controls.

---

## ⚡ Quick Runbook

### 1. Backend Service
```bash
cd backend
pip install -r requirements.txt

# Run the 7-scenario automated verification test suite
python test_verification.py

# Start the FastAPI server
uvicorn main:app --reload --port 8000
```
- API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`

### 2. Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```
- Depot Manager Dashboard: `http://localhost:3000`

---

## 🔒 Locked Project Decisions
- **PyTorch MLP Only**: No tree-based models (Random Forest / XGBoost) as per module architecture constraints.
- **Rule-Based Dispatch**: Clamped dynamic headway based on bottleneck load; no graph search or A*.
- **Data Leakage Prevention**: Chronological 80/20 train/test split by date; `ColumnTransformer` fitted strictly on train split.
- **Artifact Hygiene**: Large datasets (`.parquet`, `route100_final_dataset.csv`) and model binaries excluded via `.gitignore`.
