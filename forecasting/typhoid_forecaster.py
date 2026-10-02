import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import config
from training.train_typhoid_forecast import train_typhoid_model, load_typhoid_monthly_series


class TyphoidForecaster:
    def __init__(self, model_path: Path = None):
        self.model_path = model_path or config.TYPHOID_FORECAST_MODEL
        self.model = self._load_or_train()
        self._historical_df = None

    def _load_or_train(self):
        if self.model_path.exists():
            try:
                return joblib.load(self.model_path)
            except Exception as e:
                print(f"Warning: Failed to load {self.model_path}: {e}")

        fallback = config.BASE_DIR / "typhoid" / "typhoid_sarima_monthly.pkl"
        if fallback.exists():
            try:
                return joblib.load(fallback)
            except Exception:
                pass

        print("Typhoid model not found or corrupted. Training now...")
        return train_typhoid_model()

    @property
    def historical_data(self) -> pd.DataFrame:
        if self._historical_df is None:
            self._historical_df = load_typhoid_monthly_series()
        return self._historical_df

    def get_historical_stats(self) -> dict:
        df = self.historical_data
        mean_val = float(df["y"].mean())
        std_val = float(df["y"].std())
        return {
            "disease": "Typhoid",
            "mean": mean_val,
            "std": std_val,
            "total_months": len(df),
            "last_date": str(df["ds"].max().date()),
            "last_cases": int(df["y"].iloc[-1])
        }

    def forecast(self, steps: int = 6) -> pd.DataFrame:
        """
        Forecast Typhoid cases for the next `steps` months.
        Returns a DataFrame with columns: ['Date', 'Disease', 'Predicted_Cases'].
        """
        last_date = self.historical_data["ds"].max()
        pred_values = self.model.forecast(steps=steps)

        future_dates = pd.date_range(
            start=last_date + pd.offsets.MonthBegin(1),
            periods=steps,
            freq="MS"
        )

        forecast_df = pd.DataFrame({
            "Date": future_dates.strftime("%Y-%m-%d"),
            "Disease": "Typhoid",
            "Predicted_Cases": np.maximum(pred_values.values, 0).round().astype(int)
        })
        return forecast_df
