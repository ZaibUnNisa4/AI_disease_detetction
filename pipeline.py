"""
Unified Integrated Pipeline: AI-Based Infectious Disease Detection and Monitoring System
Integrates:
  Phase 1: Time-Series Forecasting (Dengue Holt-Winters, Typhoid SARIMA)
  Phase 2: Outbreak Anomaly & Risk Detection (Z-score thresholds)
  Phase 3: Clinical Disease Identification (SVM symptom classifier)
"""

import pandas as pd
from typing import List, Dict, Any

from forecasting.dengue_forecaster import DengueForecaster
from forecasting.typhoid_forecaster import TyphoidForecaster
from anomaly.risk_detector import RiskDetector
from identification.identifier import DiseaseIdentifier


class InfectiousDiseaseSystem:
    def __init__(self):
        print("Initializing Integrated Infectious Disease Monitoring System...")
        self.dengue_forecaster = DengueForecaster()
        self.typhoid_forecaster = TyphoidForecaster()
        self.risk_detector = RiskDetector()
        self.identifier = DiseaseIdentifier()
        print("All components initialized successfully.\n")

    def get_surveillance_forecast(self, months: int = 6, save_to_db: bool = False) -> Dict[str, Any]:
        """
        Executes Phase 1 (Forecasting) and Phase 2 (Anomaly/Risk Detection).
        Returns annotated forecasts with predicted case counts, Z-scores, and alert levels.
        Optionally persists results to Supabase.
        """
        # 1. Historical baselines
        dengue_stats = self.dengue_forecaster.get_historical_stats()
        typhoid_stats = self.typhoid_forecaster.get_historical_stats()

        # 2. Generate raw forecasts
        dengue_raw_forecast = self.dengue_forecaster.forecast(steps=months)
        typhoid_raw_forecast = self.typhoid_forecaster.forecast(steps=months)

        # 3. Apply Phase 2 risk assessment to forecasted counts
        dengue_assessed = self.risk_detector.assess_forecast(dengue_raw_forecast, dengue_stats)
        typhoid_assessed = self.risk_detector.assess_forecast(typhoid_raw_forecast, typhoid_stats)

        # 4. Identify high risk periods
        combined = pd.concat([dengue_assessed, typhoid_assessed], ignore_index=True)
        anomalies = combined[combined["Is_Anomaly"] == True]

        # 5. Optional database sync
        if save_to_db:
            try:
                from db_client import log_forecast_record, create_outbreak_alert
                for _, row in combined.iterrows():
                    date_str = str(row["Date"])[:10]
                    log_forecast_record(
                        disease=row["Disease"],
                        forecast_month=date_str,
                        predicted_cases=int(row["Predicted_Cases"]),
                        z_score=float(row["Z_Score"]),
                        risk_level=row["Risk_Level"],
                        baseline_mean=float(row["Baseline_Mean"]),
                        baseline_std=float(row["Baseline_Std"]),
                        model_name="Holt-Winters" if row["Disease"] == "Dengue" else "SARIMA"
                    )
                for _, alert in anomalies.iterrows():
                    create_outbreak_alert(
                        disease=alert["Disease"],
                        region="Surveillance Region",
                        risk_level=alert["Risk_Level"],
                        z_score=float(alert["Z_Score"]),
                        message=f"{alert['Disease']} outbreak alert for {str(alert['Date'])[:10]}: {alert['Predicted_Cases']} cases (Z={alert['Z_Score']:.2f})."
                    )
                print("Surveillance forecasts and alerts successfully synchronized to Supabase.")
            except Exception as e:
                print(f"Warning: Failed to sync forecasts to Supabase: {e}")

        return {
            "forecast_months": months,
            "baselines": {
                "Dengue": dengue_stats,
                "Typhoid": typhoid_stats
            },
            "dengue_forecast": dengue_assessed.to_dict(orient="records"),
            "typhoid_forecast": typhoid_assessed.to_dict(orient="records"),
            "combined_schedule": combined,
            "alerts": anomalies.to_dict(orient="records")
        }

    def screen_patient(
        self,
        age: float,
        gender: str,
        fever_duration: float,
        skin_manifestation: Any,
        patient_code: str = "P-AUTO",
        save_to_db: bool = False
    ) -> Dict[str, Any]:
        """
        Executes Phase 3 (Disease Identification) and contextualizes with Phase 2 Outbreak Status.
        Optionally persists clinical intake to Supabase.
        """
        # Step A: Patient symptom inference
        identification_result = self.identifier.predict_patient(
            age=age,
            gender=gender,
            fever_duration=fever_duration,
            skin_manifestation=skin_manifestation
        )
        predicted_disease = identification_result["predicted_disease"]

        # Step B: Contextualize with current surveillance baseline
        if predicted_disease == "Dengue":
            stats = self.dengue_forecaster.get_historical_stats()
        else:
            stats = self.typhoid_forecaster.get_historical_stats()

        current_risk = self.risk_detector.evaluate_case_count(
            cases=stats["last_cases"],
            mean=stats["mean"],
            std=stats["std"]
        )

        # Step C: Optional database logging
        if save_to_db:
            try:
                from db_client import log_patient_intake
                log_patient_intake(
                    patient_code=patient_code,
                    age=int(age),
                    gender=gender,
                    fever_duration=int(fever_duration),
                    skin_manifestation=bool(skin_manifestation),
                    predicted_disease=predicted_disease,
                    confidence=float(identification_result["confidence"])
                )
                print(f"Patient {patient_code} diagnosis logged to Supabase.")
            except Exception as e:
                print(f"Warning: Failed to log patient intake to Supabase: {e}")

        return {
            "clinical_diagnosis": identification_result,
            "community_surveillance_context": {
                "disease": predicted_disease,
                "latest_observed_cases": stats["last_cases"],
                "historical_mean": stats["mean"],
                "current_z_score": current_risk["z_score"],
                "current_outbreak_risk": current_risk["risk_level"],
                "is_outbreak_active": current_risk["is_anomaly"]
            }
        }


def run_full_pipeline_demo():
    system = InfectiousDiseaseSystem()

    print("=" * 65)
    print("PHASE 1 & 2: 6-MONTH OUTBREAK SURVEILLANCE & RISK FORECAST")
    print("=" * 65)
    surveillance = system.get_surveillance_forecast(months=6)

    print("\n--- DENGUE FORECAST & RISK ---")
    dengue_df = pd.DataFrame(surveillance["dengue_forecast"])
    print(dengue_df[["Date", "Predicted_Cases", "Baseline_Mean", "Z_Score", "Risk_Level"]].to_string(index=False))

    print("\n--- TYPHOID FORECAST & RISK ---")
    typhoid_df = pd.DataFrame(surveillance["typhoid_forecast"])
    print(typhoid_df[["Date", "Predicted_Cases", "Baseline_Mean", "Z_Score", "Risk_Level"]].to_string(index=False))

    if surveillance["alerts"]:
        print(f"\n[ALERT] {len(surveillance['alerts'])} upcoming anomaly/risk periods detected:")
        for alert in surveillance["alerts"]:
            print(f"  - {alert['Date']}: {alert['Disease']} -> {alert['Predicted_Cases']} cases (Z={alert['Z_Score']:.2f}, {alert['Risk_Level']})")
    else:
        print("\n[NORMAL] No critical outbreak periods detected in the next 6 months.")

    print("\n" + "=" * 65)
    print("PHASE 3: PATIENT CLINICAL SYMPTOM INTAKE & RISK CONTEXT")
    print("=" * 65)

    test_patients = [
        {"age": 28, "gender": "Male", "fever_duration": 4, "skin_manifestation": "yes", "desc": "Young male with 4-day acute fever and rash"},
        {"age": 45, "gender": "Female", "fever_duration": 14, "skin_manifestation": "no", "desc": "Adult female with 2-week prolonged fever and no rash"},
    ]

    for p in test_patients:
        res = system.screen_patient(
            age=p["age"],
            gender=p["gender"],
            fever_duration=p["fever_duration"],
            skin_manifestation=p["skin_manifestation"]
        )
        diag = res["clinical_diagnosis"]
        ctx = res["community_surveillance_context"]

        print(f"\nPatient Scenario: {p['desc']}")
        print(f"  Diagnosis:    {diag['predicted_disease']} (Confidence: {diag['confidence'] * 100:.1f}%)")
        print(f"  Probabilities: {diag['probabilities']}")
        print(f"  Community Context: Current {ctx['disease']} Risk is '{ctx['current_outbreak_risk']}' (Z={ctx['current_z_score']})")


if __name__ == "__main__":
    run_full_pipeline_demo()
