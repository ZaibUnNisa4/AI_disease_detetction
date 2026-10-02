"""
Model Training Script for Phase 1: Dengue Time-Series Forecasting
Trains Holt-Winters Exponential Smoothing model on monthly Dengue cases.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import joblib
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

import config


def load_dengue_series():
    print(f"Loading Dengue time series from: {config.DENGUE_TS_DATA}")
    df = pd.read_csv(config.DENGUE_TS_DATA)
    df["ds"] = pd.to_datetime(df["ds"])
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    df = df.dropna(subset=["ds", "y"]).sort_values("ds").reset_index(drop=True)

    print(f"Total months: {len(df)} | Start: {df['ds'].min()} | End: {df['ds'].max()}")
    return df


def train_dengue_model():
    df = load_dengue_series()
    series = df.set_index("ds")["y"]

    print("Fitting Holt-Winters model (additive seasonality, 12 periods)...")
    hw_model = ExponentialSmoothing(
        series,
        trend=None,
        seasonal="add",
        seasonal_periods=12,
        initialization_method="estimated"
    )
    fitted_model = hw_model.fit(optimized=True)

    # Validate 6-step forecast
    future_forecast = fitted_model.forecast(steps=6)
    future_dates = pd.date_range(
        start=df["ds"].max() + pd.offsets.MonthBegin(1),
        periods=6,
        freq="MS"
    )
    forecast_df = pd.DataFrame({
        "Date": future_dates,
        "Predicted_Cases": np.maximum(future_forecast.values, 0).round().astype(int)
    })
    print("\nNext 6 Months Forecast Sample:")
    print(forecast_df.to_string(index=False))

    # Save model
    save_destinations = [
        config.DENGUE_FORECAST_MODEL,
        config.BASE_DIR / "dengue" / "dengue_holt_winters_monthly.pkl"
    ]
    for p in save_destinations:
        joblib.dump(fitted_model, p)
        print(f"Saved Dengue forecast model to: {p}")

    return fitted_model


if __name__ == "__main__":
    train_dengue_model()
