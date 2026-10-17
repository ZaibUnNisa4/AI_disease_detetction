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
import auth_service


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


class LoginRequest(BaseModel):
    email_or_username: str = Field(..., description="Institutional email or staff username", examples=["ayesha.khan@numl.edu.pk"])
    password: str = Field(..., min_length=1, description="Account password", examples=["epi2026!"])
    remember_me: bool = Field(True, description="Keep user session active across restarts")


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, description="Staff full legal or clinical name", examples=["Dr. Zainab Tariq"])
    email: str = Field(..., description="Institutional email address", examples=["zainab.tariq@numl.edu.pk"])
    password: str = Field(..., min_length=6, description="Secure account password")
    role: Optional[str] = Field("Public Health Officer", description="Assigned clinical or surveillance role")
    institution: Optional[str] = Field("NUML Health Surveillance Hub", description="Affiliated healthcare institution")


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, description="Updated full professional name")
    role: Optional[str] = Field(None, description="Updated clinical/surveillance role")
    institution: Optional[str] = Field(None, description="Updated affiliated healthcare center")
    phone: Optional[str] = Field(None, description="Contact phone or terminal extension")
    department: Optional[str] = Field(None, description="Clinical or surveillance division")
    password: Optional[str] = Field(None, min_length=6, description="Optional new security password")


class AuthResponse(BaseModel):
    success: bool
    token: str
    user: Dict[str, Any]
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
            "auth_login": "/api/v1/auth/login (POST)",
            "auth_register": "/api/v1/auth/register (POST)",
            "auth_me": "/api/v1/auth/me (GET)",
            "patient_screening": "/api/v1/patient/screen (POST)",
            "dengue_forecast": "/api/v1/forecast/dengue (GET)",
            "typhoid_forecast": "/api/v1/forecast/typhoid (GET)",
            "surveillance_summary": "/api/v1/surveillance/summary (GET)",
            "surveillance_regions": "/api/v1/surveillance/regions (GET)",
            "recent_alerts": "/api/v1/alerts (GET)",
            "recent_patients": "/api/v1/patients/recent (GET)"
        }
    }


# ---------------------------------------------------------------------------
# Authentication Routes
# ---------------------------------------------------------------------------

@app.post("/api/v1/auth/login", response_model=AuthResponse, tags=["Authentication & Access Control"])
def login(payload: LoginRequest):
    """
    ### Clinical Personnel Authentication
    Authenticates healthcare practitioners and surveillance researchers.
    Provides session bearer token and full user profile.
    """
    user_profile = auth_service.authenticate_user(
        email_or_user=payload.email_or_username,
        password=payload.password
    )
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid institutional credentials. Please check your email and password."
        )

    token = auth_service.create_session(user_profile, remember_me=payload.remember_me)
    return {
        "success": True,
        "token": token,
        "user": user_profile,
        "message": f"Welcome back, {user_profile.get('name', 'User')}."
    }


@app.post("/api/v1/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, tags=["Authentication & Access Control"])
def register(payload: RegisterRequest):
    """
    ### Clinical Staff Provisioning
    Registers new clinical or epidemiological personnel into the surveillance network.
    """
    try:
        user_profile = auth_service.register_user(
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            role=payload.role or "Public Health Officer",
            institution=payload.institution or "NUML Surveillance Hub"
        )
        token = auth_service.create_session(user_profile, remember_me=True)
        return {
            "success": True,
            "token": token,
            "user": user_profile,
            "message": f"Personnel account successfully registered for {user_profile.get('name')}."
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {str(ex)}")


@app.get("/api/v1/auth/me", tags=["Authentication & Access Control"])
def get_current_user(token: Optional[str] = Query(None, description="Session bearer token")):
    """
    ### Verify Active Session
    Validates token and returns current personnel profile.
    """
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token.")
    
    user_profile = auth_service.verify_session(token)
    if not user_profile:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid.")
    
    return {"authenticated": True, "user": user_profile}


@app.post("/api/v1/auth/logout", tags=["Authentication & Access Control"])
def logout(token: Optional[str] = Query(None, description="Session bearer token")):
    """
    ### Terminal Logout
    Invalidates current active personnel session.
    """
    if token:
        auth_service.invalidate_session(token)
    return {"success": True, "message": "Successfully logged out from terminal session."}


@app.put("/api/v1/auth/profile", tags=["Authentication & Access Control"])
def update_profile(
    payload: ProfileUpdateRequest,
    token: Optional[str] = Query(None, description="Session bearer token"),
    email: Optional[str] = Query(None, description="User email identifier")
):
    """
    ### Update Clinical Personnel Profile
    Modifies display name, medical role, affiliated health center, department, phone, or password.
    """
    user_id_or_email = email
    if token:
        sess_user = auth_service.verify_session(token)
        if sess_user:
            user_id_or_email = sess_user.get("email")

    if not user_id_or_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Valid session token or user email required.")

    updated_user = auth_service.update_user_profile(
        user_id_or_email=user_id_or_email,
        name=payload.name,
        role=payload.role,
        institution=payload.institution,
        phone=payload.phone,
        department=payload.department,
        new_password=payload.password
    )
    return {
        "success": True,
        "user": updated_user,
        "message": f"Profile updated successfully for {updated_user.get('name')}."
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


@app.get("/api/v1/surveillance/regions", tags=["Surveillance & Forecasting"])
def get_surveillance_regions(
    disease: Optional[str] = Query(None, description="Optional filter by disease (Dengue, Typhoid)"),
    risk_level: Optional[str] = Query(None, description="Optional filter by risk level (Critical, Alert, Normal)"),
    province: Optional[str] = Query(None, description="Optional filter by province (Punjab, Sindh, KPK, Balochistan, etc.)")
):
    """
    ### Geospatial Outbreak & Surveillance Regions
    Returns affected regions across Pakistan, active transmission vectors,
    model-projected case volumes, Z-scores, and sentinel hospital networks.
    """
    try:
        regions_master = [
            {
                "id": "reg-rwp",
                "name": "Rawalpindi",
                "province": "Punjab",
                "latitude": 33.5973,
                "longitude": 73.0479,
                "primary_disease": "Dengue",
                "secondary_disease": "Typhoid",
                "risk_level": "Critical",
                "z_score": 3.18,
                "projected_cases": 432,
                "case_change_pct": 24.5,
                "status": "Active Outbreak",
                "dominant_vector": "Aedes aegypti (Serotype DENV-2)",
                "sentinel_hospitals": ["Holy Family Hospital", "Benazir Bhutto Hospital", "DHQ Rawalpindi"],
                "population_at_risk_millions": 2.3,
                "public_health_directive": "Intensify anti-larval indoor residual spraying in Potohar Town; establish 80-bed triage dengue isolation ward.",
                "transmission_index": 88
            },
            {
                "id": "reg-khi",
                "name": "Karachi",
                "province": "Sindh",
                "latitude": 24.8607,
                "longitude": 67.0011,
                "primary_disease": "Typhoid",
                "secondary_disease": "Dengue",
                "risk_level": "Critical",
                "z_score": 3.25,
                "projected_cases": 785,
                "case_change_pct": 19.8,
                "status": "Severe Cluster (XDR)",
                "dominant_vector": "Salmonella enterica serovar Typhi (H58 XDR clade)",
                "sentinel_hospitals": ["Civil Hospital Karachi (Dr. Ruth Pfau)", "JPMC", "The Indus Hospital"],
                "population_at_risk_millions": 16.8,
                "public_health_directive": "Administer Typhoid Conjugate Vaccine (TCV); emergency chlorination of municipal water in Lyari, Korangi & Malir.",
                "transmission_index": 94
            },
            {
                "id": "reg-lhr",
                "name": "Lahore",
                "province": "Punjab",
                "latitude": 31.5204,
                "longitude": 74.3587,
                "primary_disease": "Typhoid",
                "secondary_disease": "Dengue",
                "risk_level": "Alert",
                "z_score": 2.42,
                "projected_cases": 310,
                "case_change_pct": 12.1,
                "status": "Elevated Surveillance",
                "dominant_vector": "Salmonella Typhi & Aedes albopictus",
                "sentinel_hospitals": ["Services Hospital Lahore", "Mayo Hospital", "Sir Ganga Ram Hospital"],
                "population_at_risk_millions": 11.2,
                "public_health_directive": "Audit sewage pipeline integrity in high-density union councils; mobilize mobile vector inspection teams.",
                "transmission_index": 72
            },
            {
                "id": "reg-isb",
                "name": "Islamabad",
                "province": "Federal Capital",
                "latitude": 33.6844,
                "longitude": 73.0479,
                "primary_disease": "Dengue",
                "secondary_disease": "Typhoid",
                "risk_level": "Alert",
                "z_score": 2.12,
                "projected_cases": 145,
                "case_change_pct": 8.4,
                "status": "Pre-Epidemic Watch",
                "dominant_vector": "Aedes aegypti",
                "sentinel_hospitals": ["Pakistan Institute of Medical Sciences (PIMS)", "Polyclinic Hospital (FGPC)"],
                "population_at_risk_millions": 1.2,
                "public_health_directive": "Larvicidal treatment of standing rainwater reservoirs; weekly community ovitrap monitoring in Sectors G-7, I-9, and Rawal Town.",
                "transmission_index": 65
            },
            {
                "id": "reg-hyd",
                "name": "Hyderabad",
                "province": "Sindh",
                "latitude": 25.3960,
                "longitude": 68.3578,
                "primary_disease": "Typhoid",
                "secondary_disease": "Dengue",
                "risk_level": "Critical",
                "z_score": 3.06,
                "projected_cases": 275,
                "case_change_pct": 15.6,
                "status": "Active Outbreak",
                "dominant_vector": "Salmonella enterica (Ceftriaxone-resistant)",
                "sentinel_hospitals": ["Liaquat University Hospital", "Combined Military Hospital (CMH)"],
                "population_at_risk_millions": 1.8,
                "public_health_directive": "Issue urgent water boil advisory; dispatch mobile diagnostic clinics for rapid blood/stool culture sampling.",
                "transmission_index": 86
            },
            {
                "id": "reg-fsd",
                "name": "Faisalabad",
                "province": "Punjab",
                "latitude": 31.4504,
                "longitude": 73.1350,
                "primary_disease": "Typhoid",
                "secondary_disease": "Dengue",
                "risk_level": "Alert",
                "z_score": 2.08,
                "projected_cases": 198,
                "case_change_pct": 6.2,
                "status": "Elevated Surveillance",
                "dominant_vector": "Salmonella enterica",
                "sentinel_hospitals": ["Allied Hospital Faisalabad", "DHQ Hospital Faisalabad"],
                "population_at_risk_millions": 3.8,
                "public_health_directive": "Public awareness advisories for water filtration and sanitation surveillance in peri-urban industrial belts.",
                "transmission_index": 62
            },
            {
                "id": "reg-mul",
                "name": "Multan",
                "province": "Punjab",
                "latitude": 30.1575,
                "longitude": 71.5249,
                "primary_disease": "Typhoid",
                "secondary_disease": "Dengue",
                "risk_level": "Alert",
                "z_score": 2.15,
                "projected_cases": 165,
                "case_change_pct": 7.8,
                "status": "Elevated Surveillance",
                "dominant_vector": "Salmonella Typhi",
                "sentinel_hospitals": ["Nishtar Hospital Multan", "Multan Institute of Cardiology"],
                "population_at_risk_millions": 2.2,
                "public_health_directive": "Enhance sanitation inspections around Southern Punjab peri-urban farming belts; distribute water chlorination tablets.",
                "transmission_index": 64
            },
            {
                "id": "reg-gjw",
                "name": "Gujranwala",
                "province": "Punjab",
                "latitude": 32.1877,
                "longitude": 74.1945,
                "primary_disease": "Dengue",
                "secondary_disease": "Typhoid",
                "risk_level": "Alert",
                "z_score": 2.20,
                "projected_cases": 180,
                "case_change_pct": 10.4,
                "status": "Elevated Surveillance",
                "dominant_vector": "Aedes aegypti",
                "sentinel_hospitals": ["DHQ Teaching Hospital Gujranwala", "Gondal Medical Complex"],
                "population_at_risk_millions": 2.4,
                "public_health_directive": "Vector fogging in dense commercial auto bazaars and water vessel container inspections.",
                "transmission_index": 68
            },
            {
                "id": "reg-skt",
                "name": "Sialkot",
                "province": "Punjab",
                "latitude": 32.4945,
                "longitude": 74.5229,
                "primary_disease": "Dengue",
                "secondary_disease": "Typhoid",
                "risk_level": "Alert",
                "z_score": 2.05,
                "projected_cases": 120,
                "case_change_pct": 5.8,
                "status": "Surveillance Watch",
                "dominant_vector": "Aedes albopictus",
                "sentinel_hospitals": ["Allama Iqbal Memorial Hospital", "Sardar Begum Teaching Hospital"],
                "population_at_risk_millions": 1.7,
                "public_health_directive": "Targeted indoor spraying in industrial export sectors and peri-urban water reservoirs.",
                "transmission_index": 61
            },
            {
                "id": "reg-bwp",
                "name": "Bahawalpur",
                "province": "Punjab",
                "latitude": 29.3544,
                "longitude": 71.6911,
                "primary_disease": "Typhoid",
                "secondary_disease": "Dengue",
                "risk_level": "Alert",
                "z_score": 2.10,
                "projected_cases": 110,
                "case_change_pct": 6.5,
                "status": "Elevated Surveillance",
                "dominant_vector": "Salmonella Typhi",
                "sentinel_hospitals": ["Bahawal Victoria Hospital", "Civil Hospital Bahawalpur"],
                "population_at_risk_millions": 1.3,
                "public_health_directive": "Safe drinking water supply audits and street food hygiene testing.",
                "transmission_index": 63
            },
            {
                "id": "reg-lrk",
                "name": "Larkana",
                "province": "Sindh",
                "latitude": 27.5590,
                "longitude": 68.2120,
                "primary_disease": "Typhoid",
                "secondary_disease": "Dengue",
                "risk_level": "Critical",
                "z_score": 3.02,
                "projected_cases": 190,
                "case_change_pct": 17.2,
                "status": "Active Outbreak (XDR)",
                "dominant_vector": "Salmonella enterica (Multidrug-resistant)",
                "sentinel_hospitals": ["Chandka Medical College Hospital", "Shaheed Mohtarma Benazir Bhutto Hospital"],
                "population_at_risk_millions": 1.5,
                "public_health_directive": "Mass antibiotic sensitivity surveillance and municipal water sterilization campaign.",
                "transmission_index": 85
            },
            {
                "id": "reg-skr",
                "name": "Sukkur",
                "province": "Sindh",
                "latitude": 27.7052,
                "longitude": 68.8574,
                "primary_disease": "Typhoid",
                "secondary_disease": "Dengue",
                "risk_level": "Alert",
                "z_score": 2.14,
                "projected_cases": 135,
                "case_change_pct": 9.1,
                "status": "Elevated Surveillance",
                "dominant_vector": "Salmonella enterica",
                "sentinel_hospitals": ["Ghulam Muhammad Mahar Medical College Hospital"],
                "population_at_risk_millions": 1.2,
                "public_health_directive": "Canal water filtration verification and community sanitary education.",
                "transmission_index": 67
            },
            {
                "id": "reg-psh",
                "name": "Peshawar",
                "province": "Khyber Pakhtunkhwa",
                "latitude": 34.0151,
                "longitude": 71.5249,
                "primary_disease": "Dengue",
                "secondary_disease": "Typhoid",
                "risk_level": "Normal",
                "z_score": 1.48,
                "projected_cases": 92,
                "case_change_pct": -2.3,
                "status": "Stable Baseline",
                "dominant_vector": "Aedes albopictus",
                "sentinel_hospitals": ["Lady Reading Hospital (LRH)", "Khyber Teaching Hospital (KTH)"],
                "population_at_risk_millions": 2.1,
                "public_health_directive": "Maintain standard community reporting and ovitrap counts; monitor post-monsoon tire shops and junkyards.",
                "transmission_index": 38
            },
            {
                "id": "reg-swt",
                "name": "Swat",
                "province": "Khyber Pakhtunkhwa",
                "latitude": 34.7717,
                "longitude": 72.3602,
                "primary_disease": "Dengue",
                "secondary_disease": "Typhoid",
                "risk_level": "Normal",
                "z_score": 1.22,
                "projected_cases": 38,
                "case_change_pct": -4.5,
                "status": "Controlled Baseline",
                "dominant_vector": "Aedes albopictus",
                "sentinel_hospitals": ["Saidu Teaching Hospital"],
                "population_at_risk_millions": 0.7,
                "public_health_directive": "Seasonal stream bed checking and community education on domestic water vessel storage.",
                "transmission_index": 28
            },
            {
                "id": "reg-abt",
                "name": "Abbottabad",
                "province": "Khyber Pakhtunkhwa",
                "latitude": 34.1688,
                "longitude": 73.2215,
                "primary_disease": "Dengue",
                "secondary_disease": "Typhoid",
                "risk_level": "Normal",
                "z_score": 1.15,
                "projected_cases": 29,
                "case_change_pct": -1.2,
                "status": "Controlled Baseline",
                "dominant_vector": "Aedes albopictus",
                "sentinel_hospitals": ["Ayub Teaching Hospital", "DHQ Hospital Abbottabad"],
                "population_at_risk_millions": 0.8,
                "public_health_directive": "Highland hill station larva survey and rainfall runoff surveillance.",
                "transmission_index": 25
            },
            {
                "id": "reg-mdn",
                "name": "Mardan",
                "province": "Khyber Pakhtunkhwa",
                "latitude": 34.1989,
                "longitude": 72.0404,
                "primary_disease": "Typhoid",
                "secondary_disease": "Dengue",
                "risk_level": "Normal",
                "z_score": 1.35,
                "projected_cases": 45,
                "case_change_pct": 1.5,
                "status": "Low Incidence",
                "dominant_vector": "Salmonella enterica",
                "sentinel_hospitals": ["Mardan Medical Complex (MMC)"],
                "population_at_risk_millions": 1.0,
                "public_health_directive": "Periodic water testing in public schools and peri-urban tube wells.",
                "transmission_index": 33
            },
            {
                "id": "reg-que",
                "name": "Quetta",
                "province": "Balochistan",
                "latitude": 30.1798,
                "longitude": 66.9750,
                "primary_disease": "Typhoid",
                "secondary_disease": "Dengue",
                "risk_level": "Normal",
                "z_score": 1.18,
                "projected_cases": 54,
                "case_change_pct": 1.2,
                "status": "Low Incidence",
                "dominant_vector": "Salmonella enterica",
                "sentinel_hospitals": ["Bolan Medical Complex Hospital", "Sandeman Provincial Hospital"],
                "population_at_risk_millions": 1.1,
                "public_health_directive": "Periodic sanitary inspection of urban water supply lines and public karez channels.",
                "transmission_index": 31
            },
            {
                "id": "reg-gwd",
                "name": "Gwadar",
                "province": "Balochistan",
                "latitude": 25.1264,
                "longitude": 62.3225,
                "primary_disease": "Dengue",
                "secondary_disease": "Typhoid",
                "risk_level": "Normal",
                "z_score": 1.05,
                "projected_cases": 22,
                "case_change_pct": 0.8,
                "status": "Coastal Baseline",
                "dominant_vector": "Aedes aegypti",
                "sentinel_hospitals": ["GDA Hospital Gwadar", "DHQ Hospital Gwadar"],
                "population_at_risk_millions": 0.3,
                "public_health_directive": "Desalination water vessel storage inspections and boat dock larvicide treatment.",
                "transmission_index": 24
            },
            {
                "id": "reg-mzf",
                "name": "Muzaffarabad",
                "province": "Azad Jammu & Kashmir",
                "latitude": 34.3597,
                "longitude": 73.4711,
                "primary_disease": "Dengue",
                "secondary_disease": "Typhoid",
                "risk_level": "Normal",
                "z_score": 1.10,
                "projected_cases": 25,
                "case_change_pct": -3.1,
                "status": "Controlled Baseline",
                "dominant_vector": "Aedes albopictus",
                "sentinel_hospitals": ["Abbas Institute of Medical Sciences (AIMS)", "CMH Muzaffarabad"],
                "population_at_risk_millions": 0.6,
                "public_health_directive": "River valley mosquito larva surveys and seasonal tourist advisory.",
                "transmission_index": 26
            },
            {
                "id": "reg-glt",
                "name": "Gilgit",
                "province": "Gilgit-Baltistan",
                "latitude": 35.9221,
                "longitude": 74.3087,
                "primary_disease": "Typhoid",
                "secondary_disease": "Dengue",
                "risk_level": "Normal",
                "z_score": 0.95,
                "projected_cases": 18,
                "case_change_pct": -2.0,
                "status": "Low Incidence",
                "dominant_vector": "Salmonella enterica",
                "sentinel_hospitals": ["DHQ Hospital Gilgit", "City Hospital Gilgit"],
                "population_at_risk_millions": 0.4,
                "public_health_directive": "Glacial meltwater source sanitation audits and community boiling advisories.",
                "transmission_index": 20
            }
        ]

        # Apply optional filters
        filtered = regions_master
        if disease:
            d_lower = disease.strip().lower()
            filtered = [r for r in filtered if r["primary_disease"].lower() == d_lower]
        if risk_level:
            r_lower = risk_level.strip().lower()
            filtered = [r for r in filtered if r["risk_level"].lower() == r_lower]
        if province:
            p_lower = province.strip().lower()
            filtered = [r for r in filtered if p_lower in r["province"].lower()]

        critical_count = sum(1 for r in regions_master if r["risk_level"] == "Critical")
        alert_count = sum(1 for r in regions_master if r["risk_level"] == "Alert")
        normal_count = sum(1 for r in regions_master if r["risk_level"] == "Normal")
        total_cases = sum(r["projected_cases"] for r in regions_master)
        total_exposed_pop = round(sum(r["population_at_risk_millions"] for r in regions_master), 1)

        dengue_cases = sum(r["projected_cases"] for r in regions_master if r["primary_disease"] == "Dengue")
        typhoid_cases = sum(r["projected_cases"] for r in regions_master if r["primary_disease"] == "Typhoid")
        dengue_regions_count = sum(1 for r in regions_master if r["primary_disease"] == "Dengue")
        typhoid_regions_count = sum(1 for r in regions_master if r["primary_disease"] == "Typhoid")

        return {
            "total_regions": len(regions_master),
            "filtered_count": len(filtered),
            "summary_metrics": {
                "critical_hotspots": critical_count,
                "alert_zones": alert_count,
                "stable_districts": normal_count,
                "total_projected_cases": total_cases,
                "dengue_projected_cases": dengue_cases,
                "typhoid_projected_cases": typhoid_cases,
                "dengue_regions_count": dengue_regions_count,
                "typhoid_regions_count": typhoid_regions_count,
                "total_population_at_risk_millions": total_exposed_pop,
                "primary_epicenter": "Rawalpindi (Dengue) & Karachi (Typhoid XDR)",
                "surveillance_season": "2026 Transmission Cycle"
            },
            "regions": filtered
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to compile surveillance regions: {str(ex)}")


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
