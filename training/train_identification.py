"""
Model Training Script for Phase 3: Disease Identification (Dengue vs Typhoid)
Extracts clinical features, balances class distributions, tunes decision threshold,
and evaluates out-of-sample diagnostic performance.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_predict
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
    precision_recall_curve
)

import config


def load_and_preprocess_clinical_data(include_labs: bool = True):
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
    # PLT in Dengue dataset is in 10^9/L (x1000/uL), convert to standard counts
    d["Platelet_Count"] = pd.to_numeric(dengue_raw["PLT"], errors="coerce") * 1000.0
    d["WBC"] = pd.to_numeric(dengue_raw["WBC"], errors="coerce") * 1000.0
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
    t["Platelet_Count"] = pd.to_numeric(typhoid_raw["Platelet Count"], errors="coerce")
    t["WBC"] = pd.to_numeric(typhoid_raw["White Blood Cell Count"], errors="coerce")
    t["Disease"] = "Typhoid"

    # Keep confirmed Typhoid cases only
    confirmed_typhoid = ["Acute Typhoid Fever", "Relapsing Typhoid", "Complicated Typhoid"]
    t_confirmed = t[typhoid_raw["Typhoid Status"].isin(confirmed_typhoid)].copy()
    t_confirmed["Disease"] = "Typhoid"

    # Combine Dengue + Confirmed Typhoid
    combined = pd.concat([d, t_confirmed], ignore_index=True)

    # Impute missing values with median
    impute_cols = ["Age", "Fever_Duration", "Skin_Manifestation", "Platelet_Count", "WBC"]
    for col in impute_cols:
        combined[col] = combined[col].fillna(combined[col].median())

    features = ["Age", "Gender", "Fever_Duration", "Skin_Manifestation"]
    if include_labs:
        features.extend(["Platelet_Count", "WBC"])

    X = combined[features].copy()
    y = combined["Disease"].copy()

    print(f"Total samples: {len(X)} | Features: {features}")
    print(f"Target distribution:\n{y.value_counts()}")
    return X, y, features


def train_svm_model(include_labs: bool = False):
    """
    Trains diagnostic classifier.
    Defaults to 4 non-invasive intake features (Age, Gender, Fever_Duration, Skin_Manifestation)
    to match the clinical triage form while optimizing decision boundaries and reporting metrics.
    """
    X, y, features = load_and_preprocess_clinical_data(include_labs=include_labs)

    # Stratified Train/Test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    numeric_features = [f for f in features if f != "Gender"]
    categorical_features = ["Gender"]

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", drop="if_binary")),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipe, numeric_features),
            ("categorical", categorical_pipe, categorical_features),
        ]
    )

    # Tuned Random Forest with class balancing to prevent minority class collapse
    classifier = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        class_weight="balanced",
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", classifier)
    ])

    print("\nOptimizing decision threshold via 5-Fold Stratified Cross-Validation...")
    dengue_label = "Dengue"
    y_train_bin = (y_train == dengue_label).astype(int)

    cv_probs = cross_val_predict(pipeline, X_train, y_train_bin, cv=5, method="predict_proba")[:, 1]
    precisions, recalls, thresholds = precision_recall_curve(y_train_bin, cv_probs)
    f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)
    best_idx = int(np.argmax(f1_scores))
    optimal_threshold = float(thresholds[best_idx]) if best_idx < len(thresholds) else 0.5
    print(f"Optimal Dengue Decision Threshold: {optimal_threshold:.4f} (CV Max F1: {f1_scores[best_idx]:.4f})")

    # Fit final pipeline on training set
    print("\nFitting final model on training set...")
    pipeline.fit(X_train, y_train)

    # Evaluate on held-out test set
    classes = list(pipeline.classes_)
    dengue_idx = classes.index(dengue_label)
    test_probs = pipeline.predict_proba(X_test)[:, dengue_idx]
    y_test_bin = (y_test == dengue_label).astype(int)

    test_preds_bin = (test_probs >= optimal_threshold).astype(int)
    test_preds = np.array([dengue_label if p == 1 else ("Typhoid" if classes[0] == dengue_label else classes[0]) for p in test_preds_bin])

    acc = accuracy_score(y_test, test_preds)
    bal_acc = balanced_accuracy_score(y_test, test_preds)
    f1 = f1_score(y_test, test_preds, average="macro")
    auc = roc_auc_score(y_test_bin, test_probs)

    print("\n" + "=" * 55)
    print("HELD-OUT TEST SET EVALUATION")
    print("=" * 55)
    print(f"ROC AUC:           {auc:.4f}")
    print(f"Overall Accuracy:  {acc:.4f}")
    print(f"Balanced Accuracy: {bal_acc:.4f}")
    print(f"Macro F1 Score:    {f1:.4f}")
    print(f"Dengue Recall:     {recall_score(y_test_bin, test_preds_bin):.4f}")
    print(f"Dengue Precision:  {precision_score(y_test_bin, test_preds_bin):.4f}")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, test_preds, labels=["Typhoid", "Dengue"]))
    print("\nClassification Report:")
    print(classification_report(y_test, test_preds, digits=4))

    # Package model with metadata for inference engine
    model_payload = {
        "pipeline": pipeline,
        "features": features,
        "classes": classes,
        "dengue_index": dengue_idx,
        "optimal_threshold": optimal_threshold,
        "metrics": {
            "roc_auc": round(float(auc), 4),
            "accuracy": round(float(acc), 4),
            "macro_f1": round(float(f1), 4)
        }
    }

    # Save artifact
    save_destinations = [
        config.IDENTIFICATION_MODEL,
        config.BASE_DIR / "identification" / "disease_identification_svm.pkl"
    ]
    for p in save_destinations:
        joblib.dump(model_payload, p)
        print(f"Saved identification model artifact to: {p}")

    return model_payload


if __name__ == "__main__":
    train_svm_model()
