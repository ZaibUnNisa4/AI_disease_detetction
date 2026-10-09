"""
Database Seeding Script for NUML FYP:
AI-Based Infectious Disease Detection & Outbreak Monitoring System

Populates Supabase with:
1. Healthcare Centers (Hospitals & Surveillance Hubs)
2. 6-Month Time-Series Forecasts (Holt-Winters Dengue & SARIMA Typhoid)
3. Outbreak Anomaly Alerts (Triggered when Z >= 2.0)
4. Realistic Patient Clinical Intake Records (Processed through SVM Classifier)
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from pipeline import InfectiousDiseaseSystem
import db_client


def seed_healthcare_centers(client):
    print("\n[1/4] Seeding Healthcare Centers...")
    centers = [
        {"name": "Pakistan Institute of Medical Sciences (PIMS)", "city": "Islamabad", "district": "Islamabad", "latitude": 33.7077, "longitude": 73.0551},
        {"name": "Holy Family Hospital", "city": "Rawalpindi", "district": "Rawalpindi", "latitude": 33.6335, "longitude": 73.0673},
        {"name": "Benazir Bhutto Hospital", "city": "Rawalpindi", "district": "Rawalpindi", "latitude": 33.6067, "longitude": 73.0691},
        {"name": "Services Hospital", "city": "Lahore", "district": "Lahore", "latitude": 31.5414, "longitude": 74.3338},
        {"name": "Civil Hospital", "city": "Karachi", "district": "Karachi South", "latitude": 24.8589, "longitude": 67.0104},
    ]

    inserted_centers = []
    for c in centers:
        res = client.table("healthcare_centers").insert(c).execute()
        if res.data:
            inserted_centers.append(res.data[0])
            print(f"  + Added: {c['name']} ({c['city']})")

    print(f"Total healthcare centers seeded: {len(inserted_centers)}")
    return inserted_centers


def seed_surveillance_and_alerts(system: InfectiousDiseaseSystem):
    print("\n[2/4] Generating & Seeding 6-Month Surveillance Forecasts...")
    surveillance = system.get_surveillance_forecast(months=6, save_to_db=True)
    dengue_count = len(surveillance["dengue_forecast"])
    typhoid_count = len(surveillance["typhoid_forecast"])
    alerts_count = len(surveillance["alerts"])

    print(f"  + Dengue forecast records saved: {dengue_count}")
    print(f"  + Typhoid forecast records saved: {typhoid_count}")
    print(f"\n[3/4] Outbreak Alerts generated from Z-Score anomaly scan: {alerts_count}")
    for a in surveillance["alerts"]:
        print(f"  ! Alert: {a['Date']} - {a['Disease']} -> {a['Predicted_Cases']} cases (Z={a['Z_Score']:.2f}, {a['Risk_Level']})")

    # If no natural anomaly in the next 6 months, add a demonstration alert for surveillance readiness
    if alerts_count == 0:
        print("  * Adding demonstration high-risk alert for monitoring test...")
        db_client.create_outbreak_alert(
            disease="Dengue",
            region="Rawalpindi & Islamabad",
            risk_level="Alert",
            z_score=2.35,
            message="Post-monsoon seasonal spike warning: Elevated dengue transmission risk detected."
        )
        print("  + Added demo outbreak alert for Rawalpindi & Islamabad.")


def seed_patient_intakes(system: InfectiousDiseaseSystem, centers):
    print("\n[4/4] Processing & Seeding Patient Diagnostic Records (SVM Inference)...")
    sample_patients = [
        {"code": "PAT-ISB-001", "age": 28, "gender": "Male", "fever": 4, "rash": True, "doctor": "Dengue"},
        {"code": "PAT-RWP-002", "age": 45, "gender": "Female", "fever": 14, "rash": False, "doctor": "Typhoid"},
        {"code": "PAT-ISB-003", "age": 19, "gender": "Male", "fever": 3, "rash": True, "doctor": "Dengue"},
        {"code": "PAT-LHE-004", "age": 36, "gender": "Female", "fever": 10, "rash": False, "doctor": "Typhoid"},
        {"code": "PAT-RWP-005", "age": 52, "gender": "Male", "fever": 5, "rash": True, "doctor": "Dengue"},
        {"code": "PAT-KHI-006", "age": 23, "gender": "Female", "fever": 12, "rash": False, "doctor": "Typhoid"},
        {"code": "PAT-ISB-007", "age": 31, "gender": "Male", "fever": 2, "rash": True, "doctor": "Dengue"},
        {"code": "PAT-LHE-008", "age": 60, "gender": "Male", "fever": 16, "rash": False, "doctor": "Typhoid"},
        {"code": "PAT-RWP-009", "age": 24, "gender": "Female", "fever": 4, "rash": True, "doctor": "Dengue"},
        {"code": "PAT-KHI-010", "age": 41, "gender": "Female", "fever": 9, "rash": False, "doctor": "Typhoid"},
    ]

    for idx, p in enumerate(sample_patients):
        center_id = centers[idx % len(centers)]["id"] if centers else None
        screen_res = system.screen_patient(
            age=p["age"],
            gender=p["gender"],
            fever_duration=p["fever"],
            skin_manifestation=p["rash"]
        )
        diag = screen_res["clinical_diagnosis"]

        # Insert to database with center reference and doctor confirmed outcome
        db_client.log_patient_intake(
            patient_code=p["code"],
            age=p["age"],
            gender=p["gender"],
            fever_duration=p["fever"],
            skin_manifestation=p["rash"],
            predicted_disease=diag["predicted_disease"],
            confidence=diag["confidence"],
            center_id=center_id,
            doctor_confirmed_disease=p["doctor"]
        )
        print(f"  + [{p['code']}] Age {p['age']} {p['gender']}, Fever: {p['fever']}d, Rash: {p['rash']} -> "
              f"AI Diagnosis: {diag['predicted_disease']} ({diag['confidence'] * 100:.1f}%) [Confirmed: {p['doctor']}]")

    print(f"Total patient consultations seeded: {len(sample_patients)}")


def main():
    print("=" * 65)
    print("SUPABASE DATABASE SEEDING PROCESS")
    print("AI-Based Infectious Disease Detection & Outbreak Monitoring System")
    print("=" * 65)

    client = db_client.get_supabase_client()
    system = InfectiousDiseaseSystem()

    # 1. Centers
    centers = seed_healthcare_centers(client)

    # 2 & 3. Surveillance Forecasts & Outbreak Alerts
    seed_surveillance_and_alerts(system)

    # 4. Patient Intakes
    seed_patient_intakes(system, centers)

    print("\n" + "=" * 65)
    print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    main()
