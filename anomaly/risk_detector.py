import pandas as pd
import numpy as np
import config


def classify_zscore(z: float) -> str:
    """
    Standard Z-score classification rule used across Phase 2:
    - Normal:   Z < 2.0
    - Alert:    2.0 <= Z < 3.0
    - Critical: Z >= 3.0
    """
    if z < config.Z_ALERT_THRESHOLD:
        return "Normal"
    elif z < config.Z_CRITICAL_THRESHOLD:
        return "Alert"
    else:
        return "Critical"


class RiskDetector:
    def __init__(self, alert_threshold: float = None, critical_threshold: float = None):
        self.alert_threshold = alert_threshold or config.Z_ALERT_THRESHOLD
        self.critical_threshold = critical_threshold or config.Z_CRITICAL_THRESHOLD

    def evaluate_case_count(self, cases: float, mean: float, std: float) -> dict:
        """
        Evaluate a single case observation or predicted count against historical baseline.
        """
        std = std if std > 1e-6 else 1.0
        z_score = (cases - mean) / std
        risk_level = classify_zscore(z_score)
        is_anomaly = risk_level in ["Alert", "Critical"]

        return {
            "cases": round(cases, 1),
            "baseline_mean": round(mean, 1),
            "baseline_std": round(std, 1),
            "z_score": round(float(z_score), 2),
            "risk_level": risk_level,
            "is_anomaly": is_anomaly
        }

    def assess_forecast(self, forecast_df: pd.DataFrame, baseline_stats: dict) -> pd.DataFrame:
        """
        Annotate a forecast DataFrame with Z-score and risk classification.
        Expects columns: ['Date', 'Disease', 'Predicted_Cases'].
        """
        df = forecast_df.copy()
        mean = baseline_stats["mean"]
        std = baseline_stats["std"] if baseline_stats["std"] > 1e-6 else 1.0

        df["Baseline_Mean"] = round(mean, 1)
        df["Baseline_Std"] = round(std, 1)
        df["Z_Score"] = ((df["Predicted_Cases"] - mean) / std).round(2)
        df["Risk_Level"] = df["Z_Score"].apply(classify_zscore)
        df["Is_Anomaly"] = df["Risk_Level"].isin(["Alert", "Critical"])

        return df

    def scan_historical(self, historical_df: pd.DataFrame, disease_name: str) -> pd.DataFrame:
        """
        Scan a historical series for past anomaly events.
        Expects columns: ['ds', 'y'].
        """
        df = historical_df.copy()
        mean = df["y"].mean()
        std = df["y"].std() if df["y"].std() > 1e-6 else 1.0

        df["Disease"] = disease_name
        df["Baseline_Mean"] = round(mean, 1)
        df["Baseline_Std"] = round(std, 1)
        df["Z_Score"] = ((df["y"] - mean) / std).round(2)
        df["Risk_Level"] = df["Z_Score"].apply(classify_zscore)
        df["Is_Anomaly"] = df["Risk_Level"].isin(["Alert", "Critical"])

        return df
