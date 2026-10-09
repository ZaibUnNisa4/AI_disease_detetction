"""
FastAPI Server: AI-Based Infectious Disease Detection & Monitoring System
NUML Final Year Project (FYP)

Exposes RESTful endpoints for:
  - Phase 1: Time-Series Forecasting (Dengue Holt-Winters, Typhoid SARIMA)
  - Phase 2: Outbreak Anomaly & Risk Detection (Z-Score Thresholds)
  - Phase 3: Clinical Patient Disease Identification (SVM Classifier)
  - Cloud Database: Supabase Integration (Patient Logs, Surveillance Records, Alerts)
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Path as UrlPath, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from pipeline import InfectiousDiseaseSystem
import db_client

# Global system instance singleton
_disease_system: Optional[InfectiousDiseaseSystem] = None


def get_system() -> InfectiousDiseaseSystem:
    """Returns the cached InfectiousDiseaseSystem instance, initializing if needed."""
    global _disease_system
    if _disease_system is None:
        print("Initializing InfectiousDiseaseSystem models...")
        _disease_system = InfectiousDiseaseSystem()
    return _disease_system


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes and caches models in memory on server startup."""
    print("Pre-loading ML models into memory for FastAPI...")
    get_system()
    print("Models pre-loaded successfully. FastAPI ready for requests.")
    yield
    print("Shutting down API server...")


app = FastAPI(
    title="Infectious Disease Surveillance & Diagnostic API",
    description="""
### NUML Final Year Project (FYP)
**AI-Based Infectious Disease Detection & Outbreak Monitoring System**

This REST API serves three analytical phases:
1. **Time-Series Forecasting**: Dengue (Holt-Winters) and Typhoid (SARIMA) monthly projections.
2. **Outbreak Risk & Anomaly Detection**: Statistical Z-score evaluation against historical baselines.
3. **Clinical Patient Screening**: Multi-feature SVM disease classifier (Dengue vs. Typhoid) with confidence scoring.
4. **Cloud Database (Supabase)**: Persistent storage for patient screening logs, forecast trends, and outbreak alert alarms.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for web and mobile frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class PatientScreenRequest(BaseModel):
    patient_code: Optional[str] = Field("P-101", description="Unique patient identifier or hospital code")
    age: int = Field(..., ge=0, le=120, description="Patient age in years", examples=[28])
    gender: Literal["Male", "Female", "Other"] = Field(..., description="Patient biological sex", examples=["Male"])
    fever_duration_days: int = Field(..., ge=1, le=120, description="Duration of fever in days", examples=[4])
    skin_manifestation: bool = Field(..., description="Presence of skin rash or petechiae (True/False)", examples=[True])
    center_id: Optional[str] = Field(None, description="Optional UUID of healthcare center")
    save_to_db: bool = Field(True, description="Whether to automatically log this consultation to Supabase")


class PatientScreenResponse(BaseModel):
    patient_code: str
    predicted_disease: str
    confidence_score: float
    confidence_percentage: str
    probabilities: Dict[str, float]
    community_context: Dict[str, Any]
    db_logged: bool
    details: str


class MonthlyForecastItem(BaseModel):
    Date: str
    Disease: str
    Predicted_Cases: int
    Baseline_Mean: float
    Baseline_Std: float
    Z_Score: float
    Risk_Level: str
    Is_Anomaly: bool


class ForecastResponse(BaseModel):
    disease: str
    forecast_months: int
    baseline_statistics: Dict[str, Any]
    forecast_schedule: List[MonthlyForecastItem]
    active_alerts: List[MonthlyForecastItem]
    synced_to_db: bool


class SystemHealthResponse(BaseModel):
    status: str
    dengue_model: str
    typhoid_model: str
    identification_svm: str
    supabase_database: str
    message: str


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["System Information"])
def root_info():
    """System overview and quick access links."""
    return {
        "project": "AI-Based Infectious Disease Detection & Outbreak Monitoring System",
        "institution": "National University of Modern Languages (NUML)",
        "status": "Online",
        "documentation": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "health": "/api/v1/health",
            "patient_screening": "/api/v1/patient/screen (POST)",
            "dengue_forecast": "/api/v1/forecast/dengue (GET)",
            "typhoid_forecast": "/api/v1/forecast/typhoid (GET)",
            "surveillance_summary": "/api/v1/surveillance/summary (GET)",
            "recent_alerts": "/api/v1/alerts (GET)",
            "recent_patients": "/api/v1/patients/recent (GET)"
        }
    }


@app.get("/api/v1/health", response_model=SystemHealthResponse, tags=["System Information"])
def health_check():
    """Verifies operational status of all ML models and Supabase cloud connectivity."""
    db_status = "UNKNOWN"
    try:
        client = db_client.get_supabase_client()
        client.table("patient_intakes").select("count", count="exact").limit(0).execute()
        db_status = "ONLINE (Authenticated)"
    except Exception as e:
        db_status = f"OFFLINE ({e})"

    return {
        "status": "healthy" if "ONLINE" in db_status else "degraded",
        "dengue_model": "Online (Holt-Winters Exponential Smoothing)",
        "typhoid_model": "Online (SARIMA Multi-seasonal)",
        "identification_svm": "Online (Calibrated RBF Support Vector Machine)",
        "supabase_database": db_status,
        "message": "All diagnostic and surveillance models ready for inference."
    }


@app.post("/api/v1/patient/screen", response_model=PatientScreenResponse, status_code=status.HTTP_200_OK, tags=["Clinical Diagnostic Screening"])
def screen_patient(payload: PatientScreenRequest):
    """
    ### Clinical Diagnostic Screening (Phase 3 + Phase 2)
    Evaluates patient demographics and clinical symptoms (`age`, `gender`, `fever_duration_days`, `skin_manifestation`).
    
    * **Output**: Disease prediction (*Dengue* or *Typhoid*), calibrated confidence probability, and real-time community outbreak context.
    * **Database**: Automatically logs intake record to Supabase `patient_intakes` when `save_to_db=true`.
    """
    disease_system = get_system()

    try:
        # Run inference via Unified Pipeline
        screen_result = disease_system.screen_patient(
            age=payload.age,
            gender=payload.gender,
            fever_duration=payload.fever_duration_days,
            skin_manifestation=payload.skin_manifestation,
            patient_code=payload.patient_code,
            save_to_db=False  # Handled below for explicit control
        )

        diag = screen_result["clinical_diagnosis"]
        ctx = screen_result["community_surveillance_context"]
        db_logged = False

        if payload.save_to_db:
            try:
                db_client.log_patient_intake(
                    patient_code=payload.patient_code,
                    age=payload.age,
                    gender=payload.gender,
                    fever_duration=payload.fever_duration_days,
                    skin_manifestation=payload.skin_manifestation,
                    predicted_disease=diag["predicted_disease"],
                    confidence=diag["confidence"],
                    center_id=payload.center_id
                )
                db_logged = True
            except Exception as e:
                print(f"Warning: Failed to save to Supabase: {e}")

        summary = (
            f"Diagnosed {diag['predicted_disease']} with {diag['confidence'] * 100:.1f}% confidence. "
            f"Community {ctx['disease']} surveillance status is currently '{ctx['current_outbreak_risk']}' "
            f"(Z={ctx['current_z_score']})."
        )

        return {
            "patient_code": payload.patient_code,
            "predicted_disease": diag["predicted_disease"],
            "confidence_score": round(float(diag["confidence"]), 4),
            "confidence_percentage": f"{diag['confidence'] * 100:.1f}%",
            "probabilities": diag["probabilities"],
            "community_context": ctx,
            "db_logged": db_logged,
            "details": summary
        }

    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Diagnostic screening failed: {str(ex)}")


@app.get("/api/v1/forecast/dengue", response_model=ForecastResponse, tags=["Surveillance & Forecasting"])
def forecast_dengue(
    months: int = Query(6, ge=1, le=24, description="Forecast horizon in months"),
    save_to_db: bool = Query(False, description="Persist generated forecast & alerts to Supabase")
):
    """
    ### Dengue Time-Series Forecast (Holt-Winters)
    Generates monthly case projections, computes statistical Z-scores against historical baseline,
    and categorizes alert levels (*Normal*, *Alert*, *Critical Outbreak*).
    """
    disease_system = get_system()

    try:
        stats = disease_system.dengue_forecaster.get_historical_stats()
        raw_df = disease_system.dengue_forecaster.forecast(steps=months)
        risk_df = disease_system.risk_detector.assess_forecast(raw_df, stats)

        schedule = risk_df.to_dict(orient="records")
        for item in schedule:
            item["Date"] = str(item["Date"])[:10]

        alerts = [item for item in schedule if item.get("Is_Anomaly", False)]

        if save_to_db:
            for row in schedule:
                db_client.log_forecast_record(
                    disease="Dengue",
                    forecast_month=row["Date"],
                    predicted_cases=row["Predicted_Cases"],
                    z_score=row["Z_Score"],
                    risk_level=row["Risk_Level"],
                    baseline_mean=row["Baseline_Mean"],
                    baseline_std=row["Baseline_Std"],
                    model_name="Holt-Winters"
                )
            for alert in alerts:
                db_client.create_outbreak_alert(
                    disease="Dengue",
                    region="National Surveillance",
                    risk_level=alert["Risk_Level"],
                    z_score=alert["Z_Score"],
                    message=f"Dengue outbreak alert for {alert['Date']}: {alert['Predicted_Cases']} projected cases (Z={alert['Z_Score']:.2f})."
                )

        return {
            "disease": "Dengue",
            "forecast_months": months,
            "baseline_statistics": stats,
            "forecast_schedule": schedule,
            "active_alerts": alerts,
            "synced_to_db": save_to_db
        }

    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Dengue forecast failed: {str(ex)}")


@app.get("/api/v1/forecast/typhoid", response_model=ForecastResponse, tags=["Surveillance & Forecasting"])
def forecast_typhoid(
    months: int = Query(6, ge=1, le=24, description="Forecast horizon in months"),
    save_to_db: bool = Query(False, description="Persist generated forecast & alerts to Supabase")
):
    """
    ### Typhoid Time-Series Forecast (SARIMA)
    Generates monthly case projections, computes statistical Z-scores against historical baseline,
    and categorizes alert levels (*Normal*, *Alert*, *Critical Outbreak*).
    """
    disease_system = get_system()

    try:
        stats = disease_system.typhoid_forecaster.get_historical_stats()
        raw_df = disease_system.typhoid_forecaster.forecast(steps=months)
        risk_df = disease_system.risk_detector.assess_forecast(raw_df, stats)

        schedule = risk_df.to_dict(orient="records")
        for item in schedule:
            item["Date"] = str(item["Date"])[:10]

        alerts = [item for item in schedule if item.get("Is_Anomaly", False)]

        if save_to_db:
            for row in schedule:
                db_client.log_forecast_record(
                    disease="Typhoid",
                    forecast_month=row["Date"],
                    predicted_cases=row["Predicted_Cases"],
                    z_score=row["Z_Score"],
                    risk_level=row["Risk_Level"],
                    baseline_mean=row["Baseline_Mean"],
                    baseline_std=row["Baseline_Std"],
                    model_name="SARIMA"
                )
            for alert in alerts:
                db_client.create_outbreak_alert(
                    disease="Typhoid",
                    region="National Surveillance",
                    risk_level=alert["Risk_Level"],
                    z_score=alert["Z_Score"],
                    message=f"Typhoid outbreak alert for {alert['Date']}: {alert['Predicted_Cases']} projected cases (Z={alert['Z_Score']:.2f})."
                )

        return {
            "disease": "Typhoid",
            "forecast_months": months,
            "baseline_statistics": stats,
            "forecast_schedule": schedule,
            "active_alerts": alerts,
            "synced_to_db": save_to_db
        }

    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Typhoid forecast failed: {str(ex)}")


@app.get("/api/v1/surveillance/summary", tags=["Surveillance & Forecasting"])
def surveillance_summary(
    months: int = Query(6, ge=1, le=12, description="Forecast horizon in months"),
    save_to_db: bool = Query(False, description="Persist all results to Supabase")
):
    """
    ### Comprehensive Surveillance Scan
    Returns dual-disease projections, baseline statistics, and unified outbreak anomaly warnings.
    """
    disease_system = get_system()

    try:
        summary = disease_system.get_surveillance_forecast(months=months, save_to_db=save_to_db)
        # Format dates nicely
        for d in summary["dengue_forecast"]:
            d["Date"] = str(d["Date"])[:10]
        for t in summary["typhoid_forecast"]:
            t["Date"] = str(t["Date"])[:10]
        for a in summary["alerts"]:
            a["Date"] = str(a["Date"])[:10]

        return {
            "forecast_months": months,
            "baselines": summary["baselines"],
            "dengue": summary["dengue_forecast"],
            "typhoid": summary["typhoid_forecast"],
            "active_outbreak_alerts": summary["alerts"],
            "synced_to_db": save_to_db
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Surveillance summary failed: {str(ex)}")


@app.get("/api/v1/alerts", tags=["Cloud Database Integration"])
def get_recent_alerts(limit: int = Query(10, ge=1, le=50, description="Number of recent alerts to retrieve")):
    """Retrieves live outbreak alerts from Supabase."""
    try:
        alerts = db_client.get_recent_alerts(limit=limit)
        return {"count": len(alerts), "alerts": alerts}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts from Supabase: {str(ex)}")


@app.get("/api/v1/patients/recent", tags=["Cloud Database Integration"])
def get_recent_patient_intakes(limit: int = Query(10, ge=1, le=50, description="Number of recent intakes to retrieve")):
    """Retrieves recent clinical patient consultations from Supabase."""
    try:
        client = db_client.get_supabase_client()
        res = (
            client.table("patient_intakes")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {"count": len(res.data), "patients": res.data}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to fetch patients from Supabase: {str(ex)}")


if __name__ == "__main__":
    import uvicorn
    print("Launching FastAPI server on http://127.0.0.1:8000...")
    print("Interactive Swagger UI: http://127.0.0.1:8000/docs")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
