"""
Hybrid ETL: Kaggle public_transport.parquet → route100_final_dataset.csv
Stratified ~800k sample with Sri Lankan domain features + rain/event injection.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import holidays

SEED = 42
TARGET_ROWS = 800_000
STOPS = [
    "Panadura",
    "Moratuwa",
    "Mt_Lavinia",
    "Dehiwala",
    "Wellawatta",
    "Bambalapitiya",
    "Kollupitiya",
    "Pettah",
]
PARQUET_PATH = (
    "kaggle Public Transportation Passenger Counts dataset/public_transport.parquet"
)


def stratified_sample(df: pd.DataFrame, n: int, seed: int = SEED) -> pd.DataFrame:
    """Sample ~n rows proportional to (trip_direction, hour) strata."""
    work = df.copy()
    work["_hour"] = ((work["trip_departure"] // 3600) % 24).astype(int)
    work["_stratum"] = (
        work["trip_direction"].astype(str) + "_" + work["_hour"].astype(str)
    )

    counts = work["_stratum"].value_counts()
    alloc = (counts / counts.sum() * n).round().astype(int)
    # Fix rounding so total == n
    diff = n - int(alloc.sum())
    if diff != 0:
        order = alloc.sort_values(ascending=False).index
        for i in range(abs(diff)):
            key = order[i % len(order)]
            alloc[key] = max(0, alloc[key] + (1 if diff > 0 else -1))

    rng = np.random.default_rng(seed)
    parts: list[pd.DataFrame] = []
    for stratum, k in alloc.items():
        if k <= 0:
            continue
        group = work[work["_stratum"] == stratum]
        take = min(k, len(group))
        idx = rng.choice(group.index.to_numpy(), size=take, replace=False)
        parts.append(work.loc[idx])

    sampled = pd.concat(parts, axis=0)
    if len(sampled) > n:
        sampled = sampled.sample(n=n, random_state=seed)
    elif len(sampled) < n:
        remaining = work.drop(index=sampled.index, errors="ignore")
        need = n - len(sampled)
        if len(remaining) > 0:
            extra = remaining.sample(n=min(need, len(remaining)), random_state=seed)
            sampled = pd.concat([sampled, extra], axis=0)

    return sampled.drop(columns=["_hour", "_stratum"]).reset_index(drop=True)


def main() -> None:
    print("Loading raw data...")
    df_raw = pd.read_parquet(PARQUET_PATH)
    print(f"  raw rows: {len(df_raw):,}")

    print(f"Stratified sampling ~{TARGET_ROWS:,} rows by (direction, hour)...")
    df = stratified_sample(df_raw, TARGET_ROWS, SEED)
    print(f"  sampled rows: {len(df):,}")

    print("Mapping stops via stop_id % 8...")
    df["stop_name"] = (df["stop_id"].astype(int) % 8).map(lambda i: STOPS[i])

    print("Deriving calendar / time features from operating_day + trip_departure...")
    df["date"] = pd.to_datetime(
        df["operating_day"], format="%d.%m.%y %H:%M:%S", errors="coerce"
    )
    if df["date"].isna().mean() > 0.5:
        df["date"] = pd.to_datetime(df["operating_day"], dayfirst=True, errors="coerce")
    # Drop rows that failed date parse
    bad = df["date"].isna().sum()
    if bad:
        print(f"  dropping {bad:,} rows with unparseable operating_day")
        df = df.dropna(subset=["date"]).reset_index(drop=True)

    df["hour"] = ((df["trip_departure"] // 3600) % 24).astype(int)

    dir_vals = sorted(df["trip_direction"].dropna().unique().tolist())
    inbound_val = dir_vals[0]
    df["direction"] = np.where(
        df["trip_direction"] == inbound_val,
        "Inbound_to_Pettah",
        "Outbound_to_Panadura",
    )

    df["day_of_week"] = df["date"].dt.dayofweek  # Mon=0 … Sun=6
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    years = sorted({int(y) for y in df["date"].dt.year.unique()})
    lk_holidays = holidays.country_holidays("LK", years=years)
    df["is_public_holiday"] = df["date"].dt.date.map(
        lambda d: 1 if d in lk_holidays else 0
    )

    df["is_school_holiday"] = df["date"].dt.month.isin([4, 8, 12]).astype(int)
    df["is_payday_week"] = (
        (df["date"].dt.day >= 25) | (df["date"].dt.day <= 5)
    ).astype(int)

    df["event_override"] = 0
    df["weather"] = "Clear"
    df["passenger_count"] = df["passengers"].fillna(0).astype(int)

    rng = np.random.default_rng(SEED)

    print("Injecting events (~5%, demand x Uniform(1.8, 2.5))...")
    event_idx = df.sample(frac=0.05, random_state=SEED).index
    df.loc[event_idx, "event_override"] = 1
    boost = rng.uniform(1.8, 2.5, size=len(event_idx))
    df.loc[event_idx, "passenger_count"] = (
        df.loc[event_idx, "passenger_count"].to_numpy() * boost
    ).astype(int)

    print("Injecting rain (40% of top-quartile demand rows)...")
    threshold_75 = df["passenger_count"].quantile(0.75)
    high_demand_idx = df.index[df["passenger_count"] >= threshold_75]
    rain_idx = (
        pd.Series(high_demand_idx).sample(frac=0.40, random_state=SEED).to_numpy()
    )
    df.loc[rain_idx, "weather"] = "Rain"

    final_cols = [
        "date",
        "hour",
        "direction",
        "stop_name",
        "day_of_week",
        "is_weekend",
        "is_public_holiday",
        "is_school_holiday",
        "is_payday_week",
        "event_override",
        "weather",
        "passenger_count",
    ]
    df_final = df[final_cols].copy()
    df_final["date"] = df_final["date"].dt.strftime("%Y-%m-%d")

    out_file = "route100_final_dataset.csv"
    print(f"Exporting {len(df_final):,} rows -> {out_file}")
    df_final.to_csv(out_file, index=False)

    event_rate = df_final["event_override"].mean()
    rain_share_top = (
        df_final.loc[df_final["passenger_count"] >= threshold_75, "weather"]
        .eq("Rain")
        .mean()
    )
    print(
        f"Done. event_rate={event_rate:.3f}, "
        f"rain_in_top_quartile={rain_share_top:.3f}, "
        f"holiday_rate={df_final['is_public_holiday'].mean():.3f}"
    )


if __name__ == "__main__":
    main()
