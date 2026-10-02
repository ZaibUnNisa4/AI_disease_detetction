import os
from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).resolve().parent

# Data directory
DATA_DIR = BASE_DIR / "Datasets"

# Datasets
DENGUE_TS_DATA = DATA_DIR / "Dengue_Prophet_Cleaned.csv"
TYPHOID_SURVEILLANCE_DATA = DATA_DIR / "Typhoid_Surveillance_Clean.csv"
DENGUE_CLINICAL_DATA = DATA_DIR / "Dengue_Cleaned1.csv"
TYPHOID_CLINICAL_DATA = DATA_DIR / "typhoid_clean.csv"

# Saved models directory
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
SAVED_MODELS_DIR.mkdir(exist_ok=True)

# Model file paths
DENGUE_FORECAST_MODEL = SAVED_MODELS_DIR / "dengue_holt_winters_monthly.pkl"
TYPHOID_FORECAST_MODEL = SAVED_MODELS_DIR / "typhoid_sarima_monthly.pkl"
IDENTIFICATION_MODEL = SAVED_MODELS_DIR / "disease_identification_svm.pkl"

# Anomaly detection thresholds (Z-score)
Z_ALERT_THRESHOLD = 2.0
Z_CRITICAL_THRESHOLD = 3.0
