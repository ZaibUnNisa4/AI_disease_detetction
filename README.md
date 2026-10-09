# AI-Based Infectious Disease Detection & Monitoring System
**Final Year Project (FYP) - National University of Modern Languages (NUML)**

---

## 📌 Project Overview
This project is an end-to-end Machine Learning system engineered for the surveillance, outbreak risk detection, and clinical diagnostic identification of infectious diseases—specifically focused on **Dengue** and **Typhoid**.

The system integrates three core analytical phases into a single unified pipeline:
1. **Phase 1: Time-Series Forecasting**
   - **Dengue**: Monthly case counts forecasted using **Holt-Winters Exponential Smoothing** (Additive Trend & 12-month Additive Seasonality).
   - **Typhoid**: Monthly surveillance case counts forecasted using **SARIMA$(1, 1, 1) \times (1, 0, 1)_{12}$**.
2. **Phase 2: Outbreak Risk & Anomaly Detection**
   - Computes statistical $Z$-scores comparing forecasted and historical case volumes against baseline statistics ($\mu$, $\sigma$).
   - Categorizes risk severity levels:
     - $\text{Normal}: Z < 2.0$
     - $\text{Alert}: 2.0 \le Z < 3.0$
     - $\text{Critical Outbreak}: Z \ge 3.0$
3. **Phase 3: Patient Clinical Disease Identification**
   - A **Support Vector Machine (SVM)** classifier with balanced class weighting.
   - Evaluates readily available clinical intake features (`Age`, `Gender`, `Fever_Duration`, `Skin_Manifestation`) to rapidly distinguish between Dengue and Typhoid with calibrated confidence scores.
4. **Unified System Pipeline (`pipeline.py`)**
   - Connects community-level outbreak surveillance with individual patient intake to deliver context-aware clinical decision support.

---

## 📁 Project Structure
```text
D:\NUML_FYP\models\
│
├── Datasets\                            # Raw & cleaned clinical and surveillance datasets
│   ├── Dengue_Prophet_Cleaned.csv       # Dengue monthly time series (ds, y)
│   ├── Typhoid_Surveillance_Clean.csv   # Typhoid surveillance case records (39.8k rows)
│   ├── Dengue_Cleaned1.csv              # Dengue clinical patient records (416 samples)
│   ├── typhoid_clean.csv                # Typhoid clinical patient records (31k samples)
│   ├── Dengue_Cleaned.csv               # Dengue clinical subset
│   └── dengue.csv.csv                   # Synthetic dengue records
│
├── saved_models\                        # Production serialized model artifacts (.pkl)
│   ├── dengue_holt_winters_monthly.pkl
│   ├── typhoid_sarima_monthly.pkl
│   └── disease_identification_svm.pkl
│
├── forecasting\                         # Phase 1: Forecasting modules
│   ├── __init__.py
│   ├── dengue_forecaster.py             # Holt-Winters forecaster class
│   └── typhoid_forecaster.py            # SARIMAX forecaster class
│
├── anomaly\                             # Phase 2: Anomaly & Risk detection
│   ├── __init__.py
│   └── detector.py                      # RiskDetector (Z-score calculation & alerts)
│
├── identification\                      # Phase 3: Clinical patient identification
│   ├── __init__.py
│   ├── identifier.py                    # DiseaseIdentifier (SVM inference & confidence)
│   └── disease_identification_svm.pkl   # Local artifact copy
│
├── training\                            # Standalone, repeatable model training scripts
│   ├── __init__.py
│   ├── train_dengue_forecast.py         # Trains & evaluates Dengue Holt-Winters
│   ├── train_typhoid_forecast.py        # Aggregates & fits Typhoid SARIMAX
│   └── train_identification.py          # Preprocesses clinical data & trains SVM
│
├── config.py                            # Central paths, feature lists, and Z-score thresholds
├── pipeline.py                          # Integrated end-to-end system demo
├── interactive_cli.py                   # Interactive terminal menu for testing & demo
└── requirements.txt                     # Project dependencies
```

---

## ⚙️ Installation & Setup

### 1. Requirements
Ensure Python 3.10+ is installed. Install all required dependencies:
```bash
cd D:\NUML_FYP\models
pip install -r requirements.txt
```

---

## 🚀 How to Run the System

### Option 1: Run the Unified End-to-End Pipeline
Executes a complete surveillance scan (6-month forecast + risk detection for Dengue & Typhoid) and simulates clinical patient intake scenarios:
```bash
python pipeline.py
```

### Option 2: Run the Interactive CLI
Launch an interactive menu to test custom patient symptoms, view custom forecast horizons, or retrain models:
```bash
python interactive_cli.py
```

**Interactive Menu Options:**
- `[1]` Dengue 6-Month Forecast & Outbreak Risk Assessment
- `[2]` Typhoid 6-Month Forecast & Outbreak Risk Assessment
- `[3]` Clinical Patient Diagnosis (Interactive Intake: enter age, gender, fever days, rash)
- `[4]` Run Full System End-to-End Demo
- `[5]` Retrain Models from Datasets
- `[0]` Exit

---

### Option 3: Launch the REST API Server (FastAPI + Swagger UI)
Start the REST API server to serve model inferences over HTTP with interactive Swagger documentation:
```bash
python main.py
# Or with uvicorn directly:
uvicorn main:app --reload --port 8000
```
* **API Root**: `http://127.0.0.1:8000/`
* **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
* **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

**Available Endpoints:**
- `GET  /api/v1/health` - Operational health status of models and Supabase.
- `POST /api/v1/patient/screen` - Clinical screening (Age, Gender, Fever days, Rash) -> Diagnosis & Outbreak context.
- `GET  /api/v1/forecast/dengue` - 6-month Holt-Winters projections with Z-score outbreak classification.
- `GET  /api/v1/forecast/typhoid` - 6-month SARIMA projections with Z-score outbreak classification.
- `GET  /api/v1/surveillance/summary` - Dual-disease community surveillance scan.
- `GET  /api/v1/alerts` - Live outbreak warning alarms from Supabase.
- `GET  /api/v1/patients/recent` - Recent clinical intake records from Supabase.

---

## 🏋️‍♂️ Training Individual Models

All models can be retrained independently at any time. Generated weights are automatically saved to `saved_models/`:

### 1. Train Dengue Forecaster (Holt-Winters)
```bash
python training/train_dengue_forecast.py
```
- Fits an additive Holt-Winters model with 12-month seasonal periods on `Datasets/Dengue_Prophet_Cleaned.csv`.
- Outputs 6-month projected case counts.

### 2. Train Typhoid Forecaster (SARIMA)
```bash
python training/train_typhoid_forecast.py
```
- Aggregates confirmed cases from `Datasets/Typhoid_Surveillance_Clean.csv` into continuous monthly frequencies.
- Fits a $\text{SARIMAX}(1, 1, 1) \times (1, 0, 1)_{12}$ model and saves the fitted result.

### 3. Train Disease Identifier (SVM Classifier)
```bash
python training/train_identification.py
```
- Combines clinical records from `Dengue_Cleaned1.csv` and confirmed cases from `typhoid_clean.csv`.
- Imputes missing numerical values using median strategy.
- Uses `ColumnTransformer` with `StandardScaler` on numerical features and `OneHotEncoder` on categorical features (`Gender`).
- Fits an RBF-kernel `SVC` with `class_weight="balanced"`.
- Achieves **~86% Balanced Accuracy** and **>92% Sensitivity on Dengue**.

---

## 🔬 Methodology & Architecture

### Phase 1: Time Series Forecasting
- **Dengue**: Holt-Winters exponential smoothing accounts for recurring monsoon seasonal spikes with additive seasonal component:
  $$\hat{y}_{t+h|t} = \ell_t + h b_t + s_{t+h-m(k+1)}$$
- **Typhoid**: Seasonal Autoregressive Integrated Moving Average (SARIMA):
  $$\Phi_P(B^s)\phi_p(B)(1-B)^d(1-B^s)^D y_t = \Theta_Q(B^s)\theta_q(B)\epsilon_t$$

### Phase 2: Anomaly & Outbreak Risk Assessment
- Baseline statistics ($\mu_{\text{baseline}}, \sigma_{\text{baseline}}$) are established from historical surveillance data.
- Forecasted or observed case numbers ($y_t$) are evaluated via standard score:
  $$Z_t = \frac{y_t - \mu_{\text{baseline}}}{\sigma_{\text{baseline}}}$$
- Outbreak alarms trigger automatically when $Z \ge 2.0$.

### Phase 3: Patient Clinical Disease Identification
- Clinical intake focuses on key differentiating indicators:
  - **Fever Duration**: Dengue presents acutely (typically 2–7 days), while Typhoid presents with progressive, step-ladder prolonged fever (>7–14 days).
  - **Skin Manifestations (Rash)**: Prominent in Dengue; less frequent or distinct (rose spots) in Typhoid.
  - **Demographics**: Patient Age and Gender.
- Calibrated class probabilities provide doctors with reliable uncertainty estimates alongside the primary diagnosis.
