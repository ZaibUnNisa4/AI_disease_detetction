"""
Model Training Script for Phase 3: Disease Identification (Dengue vs Typhoid)
Extracts common clinical features and trains an SVM classifier with balanced class weights.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, classification_report, confusion_matrix

import config


def load_and_preprocess_clinical_data():
    print("Loading clinical datasets...")
    dengue_raw = pd.read_csv(config.DENGUE_CLINICAL_DATA)
    typhoid_raw = pd.read_csv(config.TYPHOID_CLINICAL_DATA)

    # 1. Dengue feature preparation
    d = pd.DataFrame()
    d["Age"] = pd.to_numeric(dengue_raw["Age"], errors="coerce")
    d["Gender"] = dengue_raw["Gender"].astype(str).str.strip().str.title()
    d["Fever"] = pd.to_numeric(dengue_raw["Fever"], errors="coerce")
    d["Fever_Duration"] = pd.to_numeric(dengue_raw["Fever_Duration"], errors="coerce")
    d["Skin_Manifestation"] = (
        dengue_raw["Rash"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"yes": 1, "no": 0})
    )
    d["WBC"] = pd.to_numeric(dengue_raw["WBC"], errors="coerce")
    d["Platelet_Count"] = pd.to_numeric(dengue_raw["PLT"], errors="coerce")
    d["Disease"] = "Dengue"

    # 2. Typhoid feature preparation
    t = pd.DataFrame()
    t["Age"] = pd.to_numeric(typhoid_raw["Age"], errors="coerce")
    t["Gender"] = typhoid_raw["Gender"].astype(str).str.strip().str.title()
    t["Fever_Duration"] = pd.to_numeric(typhoid_raw["Fever Duration (Days)"], errors="coerce")
    t["Fever"] = (t["Fever_Duration"] > 0).astype(int)
    t["Skin_Manifestation"] = (
        typhoid_raw["Skin Manifestations"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"yes": 1, "no": 0})
    )
    t["WBC"] = pd.to_numeric(typhoid_raw["White Blood Cell Count"], errors="coerce")
    t["Platelet_Count"] = pd.to_numeric(typhoid_raw["Platelet Count"], errors="coerce")
    t["Disease"] = "Typhoid"

    # Keep confirmed Typhoid cases only
    confirmed_typhoid = ["Acute Typhoid Fever", "Relapsing Typhoid", "Complicated Typhoid"]
    t_confirmed = t[typhoid_raw["Typhoid Status"].isin(confirmed_typhoid)].copy()
    t_confirmed["Disease"] = "Typhoid"

    # Combine Dengue + Confirmed Typhoid
    combined = pd.concat([d, t_confirmed], ignore_index=True)

    # Impute missing numerical values with median
    numeric_cols = ["Age", "Fever", "Fever_Duration", "Skin_Manifestation", "WBC", "Platelet_Count"]
    for col in numeric_cols:
        combined[col] = combined[col].fillna(combined[col].median())

    # Final feature set (clinical features readily available at intake)
    final_features = ["Age", "Gender", "Fever_Duration", "Skin_Manifestation"]
    X = combined[final_features].copy()
    y = combined["Disease"].copy()

    print(f"Total samples: {len(X)} | Features: {final_features}")
    print(f"Target distribution:\n{y.value_counts()}")
    return X, y


def train_svm_model():
    X, y = load_and_preprocess_clinical_data()

    # Stratified Train/Test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # Preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), ["Age", "Fever_Duration", "Skin_Manifestation"]),
            ("categorical", OneHotEncoder(handle_unknown="ignore", drop="if_binary"), ["Gender"]),
        ]
    )

    # SVM Pipeline with Platt scaling for probability estimates
    model = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", SVC(class_weight="balanced", kernel="rbf", probability=True, random_state=42)),
    ])

    print("\nFitting SVM pipeline...")
    model.fit(X_train, y_train)

    # Evaluation
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    bal_acc = balanced_accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="macro")

    print("\n" + "=" * 50)
    print("MODEL EVALUATION RESULTS")
    print("=" * 50)
    print(f"Accuracy:          {acc:.4f}")
    print(f"Balanced Accuracy: {bal_acc:.4f}")
    print(f"Macro F1 Score:    {f1:.4f}")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, digits=4))

    # Save model
    save_destinations = [
        config.IDENTIFICATION_MODEL,
        config.BASE_DIR / "identification" / "disease_identification_svm.pkl"
    ]
    for p in save_destinations:
        joblib.dump(model, p)
        print(f"Saved identification model to: {p}")

    return model


if __name__ == "__main__":
    train_svm_model()
