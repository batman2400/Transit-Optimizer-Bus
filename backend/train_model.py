"""
Train PyTorch MLP demand predictor + persist MinMax/OneHot preprocessor + metrics.
"""
from __future__ import annotations

import json
import os

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from torch.utils.data import DataLoader, TensorDataset

CATEGORICAL_FEATURES = ["direction", "stop_name", "weather"]
NUMERICAL_FEATURES = [
    "hour",
    "day_of_week",
    "is_weekend",
    "is_public_holiday",
    "is_school_holiday",
    "is_payday_week",
    "is_am_peak",
    "is_pm_peak",
    "is_school_rush",
    "month",
    "event_override",
]


class DemandPredictorMLP(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        return self.network(x)


def time_based_split(
    df: pd.DataFrame, test_size: float = 0.2
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """80/20 split by unique dates (earlier → train, later → val)."""
    dates = sorted(df["date"].unique())
    cut = max(1, int(round(len(dates) * (1.0 - test_size))))
    cut = min(cut, len(dates) - 1) if len(dates) > 1 else 1
    train_dates = set(dates[:cut])
    train_df = df[df["date"].isin(train_dates)].reset_index(drop=True)
    val_df = df[~df["date"].isin(train_dates)].reset_index(drop=True)
    if len(val_df) == 0 or len(train_df) == 0:
        # Fallback if too few unique dates
        n = len(df)
        split_i = int(n * (1.0 - test_size))
        train_df = df.iloc[:split_i].reset_index(drop=True)
        val_df = df.iloc[split_i:].reset_index(drop=True)
    return train_df, val_df


def _group_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, groups: pd.Series
) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    frame = pd.DataFrame({"y": y_true, "p": y_pred, "g": groups.astype(str).to_numpy()})
    for key, part in frame.groupby("g"):
        if len(part) < 2:
            continue
        yt = part["y"].to_numpy()
        yp = part["p"].to_numpy()
        out[str(key)] = {
            "mae": float(mean_absolute_error(yt, yp)),
            "rmse": float(np.sqrt(mean_squared_error(yt, yp))),
            "r2": float(r2_score(yt, yp)) if len(part) > 2 else float("nan"),
            "n": int(len(part)),
        }
    return out


def evaluate(y_true: np.ndarray, y_pred: np.ndarray, meta: pd.DataFrame) -> dict:
    overall = {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
        "n": int(len(y_true)),
    }
    return {
        "overall": overall,
        "by_hour": _group_metrics(y_true, y_pred, meta["hour"]),
        "by_stop": _group_metrics(y_true, y_pred, meta["stop_name"]),
        "by_weather": _group_metrics(y_true, y_pred, meta["weather"]),
        "by_weekend": _group_metrics(y_true, y_pred, meta["is_weekend"]),
        "by_public_holiday": _group_metrics(y_true, y_pred, meta["is_public_holiday"]),
        "by_payday_week": _group_metrics(y_true, y_pred, meta["is_payday_week"]),
        "by_am_peak": _group_metrics(y_true, y_pred, meta["is_am_peak"]),
        "by_pm_peak": _group_metrics(y_true, y_pred, meta["is_pm_peak"]),
        "by_school_rush": _group_metrics(y_true, y_pred, meta["is_school_rush"]),
    }


def main() -> None:
    print("Loading dataset...")
    df = pd.read_csv("route100_final_dataset.csv")
    # Ensure peak/month columns exist for older CSVs
    if "is_am_peak" not in df.columns:
        df["is_am_peak"] = df["hour"].isin([7, 8, 9]).astype(int)
    if "is_pm_peak" not in df.columns:
        df["is_pm_peak"] = df["hour"].isin([16, 17, 18, 19]).astype(int)
    if "month" not in df.columns:
        df["month"] = pd.to_datetime(df["date"]).dt.month.astype(int)
    if "is_school_rush" not in df.columns:
        term = (
            (df["is_weekend"] == 0)
            & (df["is_public_holiday"] == 0)
            & (df["is_school_holiday"] == 0)
        )
        df["is_school_rush"] = (
            df["hour"].isin([6, 7, 13, 14]) & term
        ).astype(int)

    target = "passenger_count"
    feature_cols = CATEGORICAL_FEATURES + NUMERICAL_FEATURES

    print("Time-based 80/20 split by date...")
    train_df, val_df = time_based_split(df, test_size=0.2)
    print(f"  train={len(train_df):,}  val={len(val_df):,}")

    X_train_raw = train_df[feature_cols]
    X_val_raw = val_df[feature_cols]
    y_train = train_df[target].values.astype(np.float32)
    y_val = val_df[target].values.astype(np.float32)

    print("Fitting preprocessor on train only...")
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", MinMaxScaler(), NUMERICAL_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
        ]
    )
    X_train = preprocessor.fit_transform(X_train_raw).astype(np.float32)
    X_val = preprocessor.transform(X_val_raw).astype(np.float32)

    os.makedirs("models", exist_ok=True)
    joblib.dump(preprocessor, "models/preprocessor.pkl")
    print("Preprocessor saved to models/preprocessor.pkl")

    batch_size = 512
    train_loader = DataLoader(
        TensorDataset(torch.tensor(X_train), torch.tensor(y_train).unsqueeze(1)),
        batch_size=batch_size,
        shuffle=True,
    )
    val_loader = DataLoader(
        TensorDataset(torch.tensor(X_val), torch.tensor(y_val).unsqueeze(1)),
        batch_size=batch_size,
        shuffle=False,
    )

    print("Initializing model...")
    input_dim = X_train.shape[1]
    model = DemandPredictorMLP(input_dim)

    criterion = nn.HuberLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    print(f"Device: {device} | input_dim={input_dim}")

    epochs = 100
    patience = 10
    best_val_loss = float("inf")
    epochs_no_improve = 0
    best_epoch = 0

    print("Training model...")
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * batch_X.size(0)
        train_loss /= len(train_loader.dataset)

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item() * batch_X.size(0)
        val_loss /= len(val_loader.dataset)

        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(
                f"Epoch {epoch + 1}/{epochs} - "
                f"Train Loss: {train_loss:.4f} - Val Loss: {val_loss:.4f}"
            )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            best_epoch = epoch + 1
            torch.save(
                {"state_dict": model.state_dict(), "input_dim": input_dim},
                "models/demand_predictor.pth",
            )
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"Early stopping at epoch {epoch + 1}")
                break

    # Reload best checkpoint for metrics
    checkpoint = torch.load(
        "models/demand_predictor.pth", map_location=device, weights_only=False
    )
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    with torch.no_grad():
        y_pred = (
            model(torch.tensor(X_val).to(device)).cpu().numpy().flatten()
        )

    metrics = evaluate(y_val, y_pred, val_df)
    metrics["training"] = {
        "best_val_huber": float(best_val_loss),
        "best_epoch": int(best_epoch),
        "input_dim": int(input_dim),
        "train_rows": int(len(train_df)),
        "val_rows": int(len(val_df)),
        "split": "time_based_by_date",
    }
    with open("models/metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(
        f"Training completed. Best val loss={best_val_loss:.4f} @ epoch {best_epoch}. "
        f"MAE={metrics['overall']['mae']:.2f} RMSE={metrics['overall']['rmse']:.2f} "
        f"R²={metrics['overall']['r2']:.3f}"
    )
    print("Saved models/demand_predictor.pth + models/metrics.json")


if __name__ == "__main__":
    main()
