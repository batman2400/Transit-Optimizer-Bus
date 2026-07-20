"""
==========================================================================
 AI-Powered Dynamic Public Transport Fleet Optimizer
 Phase 1 — Synthetic Data Generator
==========================================================================
 Generates a 90-day synthetic dataset (`transit_demand.csv`) for three
 bus routes. Passenger counts realistically fluctuate based on:
   • Time of day  (morning & evening rush-hour peaks)
   • Weather       (clear skies vs. rainy conditions)
   • Route-specific base demand
==========================================================================
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ── Configuration ────────────────────────────────────────────────────────
SEED = 42                       # Reproducible randomness
NUM_DAYS = 90                   # 3 months of data
START_DATE = datetime(2025, 1, 1)

# Route definitions: (route_id, route_name, base_passengers)
ROUTES = [
    ("R138", "Route 138 - City Centre <-> University",    120),
    ("R45",  "Route 45  - Airport <-> Main Station",       95),
    ("R77",  "Route 77  - Suburbs <-> Industrial Park",    70),
]

# Weather probability: 70 % clear, 30 % rainy
WEATHER_OPTIONS = ["Clear", "Rainy"]
WEATHER_PROBABILITIES = [0.70, 0.30]

# Rain increases demand (people avoid walking/cycling)
RAIN_DEMAND_MULTIPLIER = 1.25


def _hour_demand_factor(hour: int) -> float:
    """
    Return a multiplicative factor [0..1] that models the classic
    bi-modal commuter demand curve:

        Peak 1 — Morning rush   (07:00–09:00)
        Peak 2 — Evening rush   (17:00–19:00)
        Trough — Late night     (00:00–05:00)
    """
    if 7 <= hour <= 9:          # Morning rush
        return 1.0
    elif 17 <= hour <= 19:      # Evening rush
        return 0.95
    elif 10 <= hour <= 16:      # Midday — moderate demand
        return 0.55
    elif 6 == hour or 20 <= hour <= 22:  # Shoulder hours
        return 0.35
    else:                       # Late night / early morning
        return 0.10


def _is_weekend(date: datetime) -> bool:
    """Saturday = 5, Sunday = 6."""
    return date.weekday() >= 5


def generate_dataset() -> pd.DataFrame:
    """
    Build and return a DataFrame with the following columns:

        date          — YYYY-MM-DD
        day_of_week   — Monday … Sunday
        hour          — 0–23
        route_id      — R138 / R45 / R77
        route_name    — human-readable label
        weather       — Clear / Rainy
        is_weekend    — True / False
        passenger_count — synthetic ridership (integer ≥ 0)
    """
    rng = np.random.default_rng(SEED)
    records: list[dict] = []

    for day_offset in range(NUM_DAYS):
        current_date = START_DATE + timedelta(days=day_offset)
        day_name = current_date.strftime("%A")
        weekend = _is_weekend(current_date)

        # One weather assignment per day (simplification)
        weather = rng.choice(WEATHER_OPTIONS, p=WEATHER_PROBABILITIES)

        for route_id, route_name, base_passengers in ROUTES:
            for hour in range(24):
                # ── Demand calculation ───────────────────────────
                demand = base_passengers * _hour_demand_factor(hour)

                # Weekends see ~40 % less commuter traffic
                if weekend:
                    demand *= 0.60

                # Rainy weather pushes more people onto buses
                if weather == "Rainy":
                    demand *= RAIN_DEMAND_MULTIPLIER

                # Add Gaussian noise (σ = 10 % of current demand)
                noise = rng.normal(loc=0, scale=max(demand * 0.10, 1))
                demand = int(max(0, round(demand + noise)))

                records.append({
                    "date":             current_date.strftime("%Y-%m-%d"),
                    "day_of_week":      day_name,
                    "hour":             hour,
                    "route_id":         route_id,
                    "route_name":       route_name,
                    "weather":          weather,
                    "is_weekend":       weekend,
                    "passenger_count":  demand,
                })

    return pd.DataFrame(records)


# ── Main entry point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[*] Generating 90-day synthetic transit demand dataset ...")

    df = generate_dataset()

    # ── Quick sanity stats ───────────────────────────────────────────────
    total_rows = len(df)
    print(f"    - Total records generated : {total_rows:,}")
    print(f"    - Date range              : {df['date'].min()} to {df['date'].max()}")
    print(f"    - Routes                  : {df['route_id'].nunique()}")
    print(f"    - Weather split           : {df.groupby('weather')['date'].nunique().to_dict()}")
    print(f"    - Avg passengers/hour     : {df['passenger_count'].mean():.1f}")
    print(f"    - Max passengers/hour     : {df['passenger_count'].max()}")

    # ── Save to CSV ──────────────────────────────────────────────────────
    output_path = "transit_demand.csv"
    df.to_csv(output_path, index=False)
    print(f"\n[OK] Dataset saved to: {output_path}")
