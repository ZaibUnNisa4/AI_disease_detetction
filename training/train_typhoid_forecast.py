"""
Model Training Script for Phase 1: Typhoid Time-Series Forecasting
Aggregates patient-level surveillance records into monthly counts and fits SARIMAX(1,1,1)(1,0,1,12).
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import joblib
import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX

import config


def load_typhoid_monthly_series():
    print(f"Loading Typhoid surveillance dataset from: {config.TYPHOID_SURVEILLANCE_DATA}")
    df = pd.read_csv(config.TYPHOID_SURVEILLANCE_DATA)
    df["Screening_Date"] = pd.to_datetime(df["Screening_Date"])

    # Filter confirmed cases
    confirmed_df = df[df["Case_Status"].str.lower() == "confirmed"].copy()
    print(f"Total records: {len(df)} | Confirmed cases: {len(confirmed_df)}")

    # Resample to monthly counts
    monthly = (
        confirmed_df
        .set_index("Screening_Date")
        .resample("MS")
        .size()
        .reset_index(name="y")
        .rename(columns={"Screening_Date": "ds"})
    )

    # Ensure continuous monthly index
    full_range = pd.date_range(
        start=monthly["ds"].min(),
        end=monthly["ds"].max(),
        freq="MS"
    )
    monthly = (
        monthly
        .set_index("ds")
        .reindex(full_range, fill_value=0)
        .rename_axis("ds")
        .reset_index()
    )

    print(f"Total aggregated months: {len(monthly)} | Start: {monthly['ds'].min()} | End: {monthly['ds'].max()}")
    return monthly


def train_typhoid_model():
    monthly = load_typhoid_monthly_series()
    series = monthly.set_index("ds")["y"]

    print("Fitting SARIMAX(1, 1, 1)x(1, 0, 1, 12)...")
    model = SARIMAX(
        series,
        order=(1, 1, 1),
        seasonal_order=(1, 0, 1, 12),
        enforce_stationarity=False,
        enforce_invertibility=False
    )
    fitted_model = model.fit(disp=False)

    # 6-month forecast validation
    future_forecast = fitted_model.forecast(steps=6)
    future_dates = pd.date_range(
        start=monthly["ds"].max() + pd.offsets.MonthBegin(1),
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
        config.TYPHOID_FORECAST_MODEL,
        config.BASE_DIR / "typhoid" / "typhoid_sarima_monthly.pkl"
    ]
    for p in save_destinations:
        joblib.dump(fitted_model, p)
        print(f"Saved Typhoid forecast model to: {p}")

    return fitted_model


if __name__ == "__main__":
    train_typhoid_model()
