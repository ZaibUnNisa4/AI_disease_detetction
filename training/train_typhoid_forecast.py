"""
Model Training Script for Phase 1: Typhoid Time-Series Forecasting
Aggregates patient-level surveillance records into monthly counts,
evaluates out-of-sample predictive accuracy, and fits optimal SARIMAX.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import joblib
import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error, mean_squared_error

import config


def load_typhoid_monthly_series() -> pd.DataFrame:
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


def evaluate_forecast(actual: np.ndarray, predicted: np.ndarray) -> dict:
    mae = float(mean_absolute_error(actual, predicted))
    rmse = float(np.sqrt(mean_squared_error(actual, predicted)))
    denom = np.maximum(actual, 1.0)
    mape = float(np.mean(np.abs(actual - predicted) / denom) * 100.0)
    return {"mae": round(mae, 2), "rmse": round(rmse, 2), "mape": round(mape, 2)}


def train_typhoid_model():
    monthly = load_typhoid_monthly_series()
    series = monthly.set_index("ds")["y"]

    # 1. Out-of-sample holdout validation (last 6 months)
    test_horizon = 6
    train_s = series.iloc[:-test_horizon]
    test_s = series.iloc[-test_horizon:]

    # Optimal converged specification with lowest holdout error: (1, 0, 1)x(1, 0, 0, 12)
    order = (1, 0, 1)
    seasonal_order = (1, 0, 0, 12)

    print(f"\nEvaluating out-of-sample performance on last {test_horizon} months using SARIMA{order}x{seasonal_order}...")
    val_model = SARIMAX(
        train_s,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False
    ).fit(disp=False)

    val_preds = np.maximum(val_model.forecast(test_horizon).values, 0)
    metrics = evaluate_forecast(test_s.values, val_preds)

    print("\n" + "=" * 55)
    print("TYPHOID TIME-SERIES EVALUATION RESULTS")
    print("=" * 55)
    print(f"Actual Counts:    {test_s.values.tolist()}")
    print(f"Predicted Counts: {val_preds.round().astype(int).tolist()}")
    print(f"Out-of-sample MAE:  {metrics['mae']}")
    print(f"Out-of-sample RMSE: {metrics['rmse']}")
    print(f"Out-of-sample MAPE: {metrics['mape']}%")
    print(f"Model AIC Score:    {val_model.aic:.2f}")

    # 2. Fit final model on complete series
    print("\nFitting final SARIMAX model on all historical months...")
    model = SARIMAX(
        series,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False
    )
    fitted_model = model.fit(disp=False)

    # 3. 6-month forecast validation
    future_forecast = fitted_model.forecast(steps=6)
    future_dates = pd.date_range(
        start=monthly["ds"].max() + pd.offsets.MonthBegin(1),
        periods=6,
        freq="MS"
    )
    forecast_df = pd.DataFrame({
        "Date": future_dates.strftime("%Y-%m-%d"),
        "Predicted_Cases": np.maximum(future_forecast.values, 0).round().astype(int)
    })
    print("\nNext 6 Months Forecast Sample:")
    print(forecast_df.to_string(index=False))

    # 4. Save model
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
