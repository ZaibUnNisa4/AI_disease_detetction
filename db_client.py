import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Project Reference: tllwqxxnybzxcpkdpnaz
DEFAULT_SUPABASE_URL = "https://tllwqxxnybzxcpkdpnaz.supabase.co"
SUPABASE_URL = os.getenv("SUPABASE_URL", DEFAULT_SUPABASE_URL)
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Returns an authenticated Supabase client singleton."""
    global _client
    if _client is None:
        if not SUPABASE_KEY:
            raise ValueError(
                "Missing SUPABASE_SERVICE_KEY or SUPABASE_KEY. "
                "Please add your project API key to D:\\NUML_FYP\\models\\.env"
            )
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def log_patient_intake(
    patient_code: str,
    age: int,
    gender: str,
    fever_duration: int,
    skin_manifestation: bool,
    predicted_disease: str,
    confidence: float,
    center_id: Optional[str] = None,
    doctor_confirmed_disease: Optional[str] = None
) -> Dict[str, Any]:
    """
    Logs Phase 3 SVM clinical diagnosis output to Supabase patient_intakes table.
    """
    client = get_supabase_client()
    data = {
        "patient_code": patient_code,
        "age": int(age),
        "gender": gender,
        "fever_duration_days": int(fever_duration),
        "skin_manifestation": bool(skin_manifestation),
        "predicted_disease": predicted_disease,
        "confidence_score": round(float(confidence), 4),
    }
    if center_id:
        data["center_id"] = center_id
    if doctor_confirmed_disease:
        data["doctor_confirmed_disease"] = doctor_confirmed_disease

    response = client.table("patient_intakes").insert(data).execute()
    return response.data


def log_forecast_record(
    disease: str,
    forecast_month: str,
    predicted_cases: int,
    z_score: float,
    risk_level: str,
    baseline_mean: Optional[float] = None,
    baseline_std: Optional[float] = None,
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Logs Phase 1 & 2 forecast and risk classification to surveillance_forecasts table.
    """
    client = get_supabase_client()
    data = {
        "disease": disease,
        "forecast_month": forecast_month,
        "predicted_cases": int(predicted_cases),
        "z_score": round(float(z_score), 3),
        "risk_level": risk_level,
    }
    if baseline_mean is not None:
        data["baseline_mean"] = round(float(baseline_mean), 2)
    if baseline_std is not None:
        data["baseline_std"] = round(float(baseline_std), 2)
    if model_name:
        data["model_name"] = model_name

    response = client.table("surveillance_forecasts").insert(data).execute()
    return response.data


def create_outbreak_alert(
    disease: str,
    region: str,
    risk_level: str,
    z_score: float,
    message: str
) -> Dict[str, Any]:
    """
    Creates an outbreak alert in outbreak_alerts table when Z >= 2.0.
    """
    client = get_supabase_client()
    data = {
        "disease": disease,
        "region": region,
        "risk_level": risk_level,
        "z_score": round(float(z_score), 3),
        "alert_message": message,
        "is_resolved": False
    }
    response = client.table("outbreak_alerts").insert(data).execute()
    return response.data


def get_recent_alerts(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieves recent active outbreak alerts."""
    client = get_supabase_client()
    response = (
        client.table("outbreak_alerts")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data
