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
        Annotate a forecast DataFrame with seasonally-adjusted or global Z-score and risk classification.
        Expects columns: ['Date', 'Disease', 'Predicted_Cases'].
        """
        df = forecast_df.copy()
        seasonal = baseline_stats.get("seasonal_baselines", {})

        baseline_means = []
        baseline_stds = []
        z_scores = []

        for _, row in df.iterrows():
            m_mean = baseline_stats.get("mean", 0.0)
            m_std = baseline_stats.get("std", 1.0)

            if seasonal:
                try:
                    month_num = pd.to_datetime(row["Date"]).month
                    if month_num in seasonal:
                        m_mean = seasonal[month_num].get("mean", m_mean)
                        m_std = seasonal[month_num].get("std", m_std)
                except Exception:
                    pass

            m_std = m_std if m_std > 1e-6 else 1.0
            z = (row["Predicted_Cases"] - m_mean) / m_std

            baseline_means.append(round(m_mean, 1))
            baseline_stds.append(round(m_std, 1))
            z_scores.append(round(float(z), 2))

        df["Baseline_Mean"] = baseline_means
        df["Baseline_Std"] = baseline_stds
        df["Z_Score"] = z_scores
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
