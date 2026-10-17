"""
Model Training Script for Phase 1: Dengue Time-Series Forecasting
Trains and evaluates Holt-Winters Exponential Smoothing on monthly Dengue cases
with out-of-sample validation metrics (MAE, RMSE, MAPE) and seasonal baseline computation.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import joblib
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_absolute_error, mean_squared_error

import config


def load_dengue_series() -> pd.DataFrame:
    print(f"Loading Dengue time series from: {config.DENGUE_TS_DATA}")
    df = pd.read_csv(config.DENGUE_TS_DATA)
    df["ds"] = pd.to_datetime(df["ds"])
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    df = df.dropna(subset=["ds", "y"]).sort_values("ds").reset_index(drop=True)

    print(f"Total months: {len(df)} | Start: {df['ds'].min()} | End: {df['ds'].max()}")
    return df


def evaluate_forecast(actual: np.ndarray, predicted: np.ndarray) -> dict:
    mae = float(mean_absolute_error(actual, predicted))
    rmse = float(np.sqrt(mean_squared_error(actual, predicted)))
    denom = np.maximum(actual, 1.0)
    mape = float(np.mean(np.abs(actual - predicted) / denom) * 100.0)
    return {"mae": round(mae, 2), "rmse": round(rmse, 2), "mape": round(mape, 2)}


def train_dengue_model():
    df = load_dengue_series()
    series = df.set_index("ds")["y"]

    # 1. Out-of-sample validation (hold out last 6 months)
    test_horizon = 6
    if len(series) > test_horizon + 12:
        train_s = series.iloc[:-test_horizon]
        test_s = series.iloc[-test_horizon:]

        print(f"\nEvaluating out-of-sample performance on last {test_horizon} months...")
        val_model = ExponentialSmoothing(
            train_s,
            trend=None,
            seasonal="add",
            seasonal_periods=12,
            initialization_method="estimated"
        ).fit(optimized=True)

        val_preds = np.maximum(val_model.forecast(test_horizon).values, 0)
        metrics = evaluate_forecast(test_s.values, val_preds)

        print("\n" + "=" * 55)
        print("DENGUE TIME-SERIES EVALUATION RESULTS")
        print("=" * 55)
        print(f"Actual Counts:    {test_s.values.tolist()}")
        print(f"Predicted Counts: {val_preds.round().astype(int).tolist()}")
        print(f"Out-of-sample MAE:  {metrics['mae']}")
        print(f"Out-of-sample RMSE: {metrics['rmse']}")
        print(f"Out-of-sample MAPE: {metrics['mape']}%")
    else:
        metrics = {"mae": None, "rmse": None, "mape": None}

    # 2. Fit final model on complete dataset
    print("\nFitting final Holt-Winters model on all historical months...")
    hw_model = ExponentialSmoothing(
        series,
        trend=None,
        seasonal="add",
        seasonal_periods=12,
        initialization_method="estimated"
    )
    fitted_model = hw_model.fit(optimized=True)

    # 3. Compute month-of-year seasonal statistics for epidemiological anomaly detection
    df_stats = df.copy()
    df_stats["month"] = df_stats["ds"].dt.month
    monthly_seasonal_stats = {}
    for m in range(1, 13):
        m_vals = df_stats[df_stats["month"] == m]["y"]
        if len(m_vals) > 0:
            monthly_seasonal_stats[m] = {
                "mean": round(float(m_vals.mean()), 1),
                "std": round(float(m_vals.std()) if len(m_vals) > 1 else float(m_vals.mean() * 0.2), 1),
                "count": len(m_vals)
            }
        else:
            monthly_seasonal_stats[m] = {
                "mean": round(float(df["y"].mean()), 1),
                "std": round(float(df["y"].std()), 1),
                "count": 0
            }

    # 4. Generate next 6 months projection sample
    future_forecast = fitted_model.forecast(steps=6)
    future_dates = pd.date_range(
        start=df["ds"].max() + pd.offsets.MonthBegin(1),
        periods=6,
        freq="MS"
    )
    forecast_df = pd.DataFrame({
        "Date": future_dates.strftime("%Y-%m-%d"),
        "Predicted_Cases": np.maximum(future_forecast.values, 0).round().astype(int)
    })
    print("\nNext 6 Months Forecast Projections:")
    print(forecast_df.to_string(index=False))

    # 5. Save model bundle
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
