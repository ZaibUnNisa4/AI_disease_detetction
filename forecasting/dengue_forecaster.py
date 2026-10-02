import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import config
from training.train_dengue_forecast import train_dengue_model, load_dengue_series


class DengueForecaster:
    def __init__(self, model_path: Path = None):
        self.model_path = model_path or config.DENGUE_FORECAST_MODEL
        self.model = self._load_or_train()
        self._historical_df = None

    def _load_or_train(self):
        # Try primary path
        if self.model_path.exists():
            try:
                return joblib.load(self.model_path)
            except Exception as e:
                print(f"Warning: Failed to load {self.model_path}: {e}")

        # Try secondary fallback path
        fallback = config.BASE_DIR / "dengue" / "dengue_holt_winters_monthly.pkl"
        if fallback.exists():
            try:
                return joblib.load(fallback)
            except Exception:
                pass

        # If not found or broken, train on the fly
        print("Dengue model not found or corrupted. Training now...")
        return train_dengue_model()

    @property
    def historical_data(self) -> pd.DataFrame:
        if self._historical_df is None:
            self._historical_df = load_dengue_series()
        return self._historical_df

    def get_historical_stats(self) -> dict:
        df = self.historical_data
        mean_val = float(df["y"].mean())
        std_val = float(df["y"].std())
        return {
            "disease": "Dengue",
            "mean": mean_val,
            "std": std_val,
            "total_months": len(df),
            "last_date": str(df["ds"].max().date()),
            "last_cases": int(df["y"].iloc[-1])
        }

    def forecast(self, steps: int = 6) -> pd.DataFrame:
        """
        Forecast Dengue cases for the next `steps` months.
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
            "Disease": "Dengue",
            "Predicted_Cases": np.maximum(pred_values.values, 0).round().astype(int)
        })
        return forecast_df
