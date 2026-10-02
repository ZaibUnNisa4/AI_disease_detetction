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
    print("DENGUE 6-MONTH TIME-SERIES FORECAST & RISK SCAN")
    print("-" * 50)
    try:
        steps = input("Enter forecast horizon in months [default: 6]: ").strip()
        steps = int(steps) if steps else 6
    except ValueError:
        steps = 6

    forecast_df = system.dengue_forecaster.forecast_monthly(steps=steps)
    risk_df = system.risk_detector.assess_forecast(forecast_df, "Dengue")
    print("\nForecast Results:")
    print(risk_df.to_string(index=False))


def handle_typhoid_forecast(system: InfectiousDiseaseSystem):
    print("\n" + "-" * 50)
    print("TYPHOID 6-MONTH TIME-SERIES FORECAST & RISK SCAN")
    print("-" * 50)
    try:
        steps = input("Enter forecast horizon in months [default: 6]: ").strip()
        steps = int(steps) if steps else 6
    except ValueError:
        steps = 6

    forecast_df = system.typhoid_forecaster.forecast_monthly(steps=steps)
    risk_df = system.risk_detector.assess_forecast(forecast_df, "Typhoid")
    print("\nForecast Results:")
    print(risk_df.to_string(index=False))


def handle_patient_intake(system: InfectiousDiseaseSystem):
    print("\n" + "-" * 50)
    print("PATIENT CLINICAL INTAKE (DISEASE IDENTIFICATION)")
    print("-" * 50)
    try:
        age_str = input("Enter Patient Age [e.g. 25]: ").strip()
        age = float(age_str) if age_str else 25.0

        gender = input("Enter Patient Gender (Male/Female) [default: Male]: ").strip()
        if not gender:
            gender = "Male"

        fever_str = input("Enter Fever Duration in Days [e.g. 4]: ").strip()
        fever_duration = float(fever_str) if fever_str else 4.0

        rash_str = input("Does the patient have rash/skin manifestation? (yes/no) [default: yes]: ").strip()
        skin_manifestation = rash_str.lower() in ["yes", "y", "true", "1"] if rash_str else True

        result = system.diagnose_patient_with_risk_context(
            age=age,
            gender=gender,
            fever_duration=fever_duration,
            skin_manifestation=skin_manifestation
        )

        diag = result["patient_diagnosis"]
        ctx = result["community_risk_context"]

        print("\n" + "=" * 50)
        print("DIAGNOSTIC REPORT")
        print("=" * 50)
        print(f"Predicted Disease:     {diag['predicted_disease']}")
        print(f"Confidence:            {diag['confidence'] * 100:.1f}%")
        print(f"Class Probabilities:   {diag['probabilities']}")
        print("\nCommunity Outbreak Context:")
        print(f"  Current Dengue Risk:  {ctx['dengue']['current_risk_level']} (Z={ctx['dengue']['latest_z_score']:.2f})")
        print(f"  Current Typhoid Risk: {ctx['typhoid']['current_risk_level']} (Z={ctx['typhoid']['latest_z_score']:.2f})")
        print(f"  Overall Community Alert: {ctx['overall_alert']}")
        print("=" * 50)

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
            system.run_full_surveillance_pipeline()
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
