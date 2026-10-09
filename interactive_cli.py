"""
Interactive CLI for Final Year Project (FYP):
AI-Based Infectious Disease Detection & Monitoring System
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from pipeline import InfectiousDiseaseSystem
import config


def print_banner():
    print("=" * 70)
    print("  AI-BASED INFECTIOUS DISEASE DETECTION & MONITORING SYSTEM (FYP)")
    print("  NUML Final Year Project - Dengue & Typhoid Surveillance")
    print("=" * 70)


def print_menu():
    print("\nSelect an option:")
    print("  [1] Dengue 6-Month Forecast & Outbreak Risk Assessment")
    print("  [2] Typhoid 6-Month Forecast & Outbreak Risk Assessment")
    print("  [3] Clinical Patient Diagnosis (Interactive Intake)")
    print("  [4] Run Full System End-to-End Demo")
    print("  [5] Retrain Models from Datasets")
    print("  [0] Exit")


def handle_dengue_forecast(system: InfectiousDiseaseSystem):
    print("\n" + "-" * 50)
    print("DENGUE TIME-SERIES FORECAST & RISK SCAN")
    print("-" * 50)
    try:
        steps = input("Enter forecast horizon in months [default: 6]: ").strip()
        steps = int(steps) if steps else 6
    except ValueError:
        steps = 6

    stats = system.dengue_forecaster.get_historical_stats()
    forecast_df = system.dengue_forecaster.forecast(steps=steps)
    risk_df = system.risk_detector.assess_forecast(forecast_df, stats)
    print("\nForecast Results:")
    print(risk_df.to_string(index=False))

    save_db = input("\nSave forecast records to Supabase? (y/n) [default: n]: ").strip().lower()
    if save_db in ["y", "yes"]:
        try:
            from db_client import log_forecast_record, create_outbreak_alert
            count = 0
            for _, row in risk_df.iterrows():
                # Format date to YYYY-MM-01
                date_str = str(row["Date"])[:10]
                log_forecast_record(
                    disease="Dengue",
                    forecast_month=date_str,
                    predicted_cases=int(row["Predicted_Cases"]),
                    z_score=float(row["Z_Score"]),
                    risk_level=row["Risk_Level"],
                    baseline_mean=float(row["Baseline_Mean"]),
                    baseline_std=float(row["Baseline_Std"]),
                    model_name="Holt-Winters"
                )
                if row.get("Is_Anomaly", False):
                    create_outbreak_alert(
                        disease="Dengue",
                        region="Surveillance Region",
                        risk_level=row["Risk_Level"],
                        z_score=float(row["Z_Score"]),
                        message=f"Dengue outbreak warning for {date_str}: {row['Predicted_Cases']} cases predicted (Z={row['Z_Score']:.2f})."
                    )
                count += 1
            print(f"Logged {count} forecast records and active alerts to Supabase!")
        except Exception as e:
            print(f"Error logging to Supabase: {e}")


def handle_typhoid_forecast(system: InfectiousDiseaseSystem):
    print("\n" + "-" * 50)
    print("TYPHOID TIME-SERIES FORECAST & RISK SCAN")
    print("-" * 50)
    try:
        steps = input("Enter forecast horizon in months [default: 6]: ").strip()
        steps = int(steps) if steps else 6
    except ValueError:
        steps = 6

    stats = system.typhoid_forecaster.get_historical_stats()
    forecast_df = system.typhoid_forecaster.forecast(steps=steps)
    risk_df = system.risk_detector.assess_forecast(forecast_df, stats)
    print("\nForecast Results:")
    print(risk_df.to_string(index=False))

    save_db = input("\nSave forecast records to Supabase? (y/n) [default: n]: ").strip().lower()
    if save_db in ["y", "yes"]:
        try:
            from db_client import log_forecast_record, create_outbreak_alert
            count = 0
            for _, row in risk_df.iterrows():
                date_str = str(row["Date"])[:10]
                log_forecast_record(
                    disease="Typhoid",
                    forecast_month=date_str,
                    predicted_cases=int(row["Predicted_Cases"]),
                    z_score=float(row["Z_Score"]),
                    risk_level=row["Risk_Level"],
                    baseline_mean=float(row["Baseline_Mean"]),
                    baseline_std=float(row["Baseline_Std"]),
                    model_name="SARIMA"
                )
                if row.get("Is_Anomaly", False):
                    create_outbreak_alert(
                        disease="Typhoid",
                        region="Surveillance Region",
                        risk_level=row["Risk_Level"],
                        z_score=float(row["Z_Score"]),
                        message=f"Typhoid outbreak warning for {date_str}: {row['Predicted_Cases']} cases predicted (Z={row['Z_Score']:.2f})."
                    )
                count += 1
            print(f"Logged {count} forecast records and active alerts to Supabase!")
        except Exception as e:
            print(f"Error logging to Supabase: {e}")


def handle_patient_intake(system: InfectiousDiseaseSystem):
    print("\n" + "-" * 50)
    print("PATIENT CLINICAL INTAKE (DISEASE IDENTIFICATION)")
    print("-" * 50)
    try:
        patient_code = input("Enter Patient ID/Code [default: P-001]: ").strip()
        if not patient_code:
            patient_code = "P-001"

        age_str = input("Enter Patient Age [e.g. 25]: ").strip()
        age = float(age_str) if age_str else 25.0

        gender = input("Enter Patient Gender (Male/Female) [default: Male]: ").strip().capitalize()
        if gender not in ["Male", "Female"]:
            gender = "Male"

        fever_str = input("Enter Fever Duration in Days [e.g. 4]: ").strip()
        fever_duration = float(fever_str) if fever_str else 4.0

        rash_str = input("Does the patient have rash/skin manifestation? (yes/no) [default: yes]: ").strip()
        skin_manifestation = rash_str.lower() in ["yes", "y", "true", "1"] if rash_str else True

        result = system.screen_patient(
            age=age,
            gender=gender,
            fever_duration=fever_duration,
            skin_manifestation=skin_manifestation
        )

        diag = result["clinical_diagnosis"]
        ctx = result["community_surveillance_context"]

        print("\n" + "=" * 50)
        print("DIAGNOSTIC REPORT")
        print("=" * 50)
        print(f"Patient Code:          {patient_code}")
        print(f"Predicted Disease:     {diag['predicted_disease']}")
        print(f"Confidence:            {diag['confidence'] * 100:.1f}%")
        print(f"Class Probabilities:   {diag['probabilities']}")
        print("\nCommunity Outbreak Context:")
        print(f"  Disease Context:      {ctx['disease']}")
        print(f"  Current Risk Level:   {ctx['current_outbreak_risk']} (Z={ctx['current_z_score']})")
        print(f"  Active Outbreak:      {ctx['is_outbreak_active']}")
        print("=" * 50)

        save_db = input("\nSave patient diagnosis to Supabase? (y/n) [default: y]: ").strip().lower()
        if save_db not in ["n", "no"]:
            try:
                from db_client import log_patient_intake
                rec = log_patient_intake(
                    patient_code=patient_code,
                    age=int(age),
                    gender=gender,
                    fever_duration=int(fever_duration),
                    skin_manifestation=bool(skin_manifestation),
                    predicted_disease=diag["predicted_disease"],
                    confidence=float(diag["confidence"])
                )
                print("Patient intake record successfully saved to Supabase!")
            except Exception as e:
                print(f"Error logging to Supabase: {e}")

    except Exception as e:
        print(f"Error during patient intake: {e}")


def handle_retrain():
    print("\n" + "-" * 50)
    print("RETRAINING ALL MODELS")
    print("-" * 50)
    from training.train_dengue_forecast import train_dengue_model
    from training.train_typhoid_forecast import train_typhoid_model
    from training.train_identification import train_svm_model

    print("\n[1/3] Training Dengue Holt-Winters Model...")
    train_dengue_model()

    print("\n[2/3] Training Typhoid SARIMA Model...")
    train_typhoid_model()

    print("\n[3/3] Training Disease Identification SVM...")
    train_svm_model()

    print("\nAll models retrained successfully!")


def main():
    print_banner()
    print("Loading system models and baselines...")
    system = InfectiousDiseaseSystem()
    print("System ready!")

    while True:
        print_menu()
        choice = input("\nEnter choice [0-5]: ").strip()

        if choice == "1":
            handle_dengue_forecast(system)
        elif choice == "2":
            handle_typhoid_forecast(system)
        elif choice == "3":
            handle_patient_intake(system)
        elif choice == "4":
            from pipeline import run_full_pipeline_demo
            run_full_pipeline_demo()
        elif choice == "5":
            handle_retrain()
            # Reload models
            system = InfectiousDiseaseSystem()
        elif choice == "0":
            print("\nExiting. Thank you!")
            break
        else:
            print("\nInvalid choice. Please select from 0 to 5.")


if __name__ == "__main__":
    main()
