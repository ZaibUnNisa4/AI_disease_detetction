import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import config
from training.train_identification import train_svm_model


class DiseaseIdentifier:
    def __init__(self, model_path: Path = None):
        self.model_path = model_path or config.IDENTIFICATION_MODEL
        self.raw_artifact = self._load_or_train()
        self._unpack_model()

    def _unpack_model(self):
        """Unpacks pipeline and threshold metadata from artifact."""
        if isinstance(self.raw_artifact, dict) and "pipeline" in self.raw_artifact:
            self.pipeline = self.raw_artifact["pipeline"]
            self.optimal_threshold = float(self.raw_artifact.get("optimal_threshold", 0.5))
            self.classes = list(self.raw_artifact.get("classes", ["Dengue", "Typhoid"]))
            self.dengue_index = int(self.raw_artifact.get("dengue_index", self.classes.index("Dengue") if "Dengue" in self.classes else 0))
            self.feature_names = self.raw_artifact.get("features", ["Age", "Gender", "Fever_Duration", "Skin_Manifestation"])
            self.metrics = self.raw_artifact.get("metrics", {})
        else:
            self.pipeline = self.raw_artifact
            self.optimal_threshold = 0.5
            self.classes = list(getattr(self.pipeline, "classes_", ["Dengue", "Typhoid"]))
            self.dengue_index = self.classes.index("Dengue") if "Dengue" in self.classes else 0
            self.feature_names = ["Age", "Gender", "Fever_Duration", "Skin_Manifestation"]
            self.metrics = {}

    def _load_or_train(self):
        # 1. Check primary saved models path
        if self.model_path.exists():
            try:
                return joblib.load(self.model_path)
            except Exception as e:
                print(f"Notice: Primary model at {self.model_path} cannot be unpickled ({e}).")

        # 2. Check fallback location
        fallback = config.BASE_DIR / "identification" / "disease_identification_svm.pkl"
        if fallback.exists() and fallback != self.model_path:
            try:
                return joblib.load(fallback)
            except Exception:
                pass

        # 3. Train on the fly and persist
        print("Training fresh diagnostic model locally using available datasets...")
        return train_svm_model()

    def _clean_input(
        self,
        age: float,
        gender: str,
        fever_duration: float,
        skin_manifestation,
        platelet_count: float = None,
        wbc_count: float = None
    ) -> pd.DataFrame:
        clean_gender = str(gender).strip().title()
        if clean_gender not in ["Male", "Female"]:
            clean_gender = "Male" if clean_gender.lower().startswith("m") else "Female"

        if isinstance(skin_manifestation, bool):
            clean_skin = 1 if skin_manifestation else 0
        elif isinstance(skin_manifestation, (int, float)):
            clean_skin = 1 if skin_manifestation > 0 else 0
        else:
            clean_skin = 1 if str(skin_manifestation).strip().lower() in ["yes", "y", "true", "1", "rash"] else 0

        data = {
            "Age": [float(age)],
            "Gender": [clean_gender],
            "Fever_Duration": [float(fever_duration)],
            "Skin_Manifestation": [clean_skin]
        }

        # Include optional laboratory markers if expected by pipeline
        if "Platelet_Count" in self.feature_names:
            data["Platelet_Count"] = [float(platelet_count) if platelet_count is not None else np.nan]
        if "WBC" in self.feature_names:
            data["WBC"] = [float(wbc_count) if wbc_count is not None else np.nan]

        return pd.DataFrame(data)

    def predict_patient(
        self,
        age: float,
        gender: str,
        fever_duration: float,
        skin_manifestation,
        platelet_count: float = None,
        wbc_count: float = None
    ) -> dict:
        """
        Predict whether patient symptoms correspond to Dengue or Typhoid with calibrated probabilities.
        """
        input_df = self._clean_input(age, gender, fever_duration, skin_manifestation, platelet_count, wbc_count)

        if hasattr(self.pipeline, "predict_proba"):
            raw_probs = self.pipeline.predict_proba(input_df)[0]
            classes = list(getattr(self.pipeline, "classes_", self.classes))
            probs = {cls: round(float(prob), 4) for cls, prob in zip(classes, raw_probs)}

            d_idx = classes.index("Dengue") if "Dengue" in classes else self.dengue_index
            t_idx = 1 - d_idx if len(classes) == 2 else 0

            # Apply optimized threshold for balanced diagnosis
            dengue_prob = raw_probs[d_idx]
            if dengue_prob >= self.optimal_threshold:
                pred_label = "Dengue"
                confidence = round(float(dengue_prob), 4)
            else:
                pred_label = classes[t_idx]
                confidence = round(float(raw_probs[t_idx]), 4)
        else:
            pred_label = self.pipeline.predict(input_df)[0]
            probs = {"Dengue": 0.5, "Typhoid": 0.5}
            confidence = 0.5

        return {
            "predicted_disease": pred_label,
            "confidence": confidence,
            "probabilities": probs,
            "patient_features": {
                "age": float(age),
                "gender": input_df["Gender"].iloc[0],
                "fever_duration_days": float(fever_duration),
                "skin_manifestation": bool(input_df["Skin_Manifestation"].iloc[0]),
                "platelet_count": float(platelet_count) if platelet_count is not None else None,
                "wbc_count": float(wbc_count) if wbc_count is not None else None
            }
        }

    def predict_batch(self, patients_df: pd.DataFrame) -> pd.DataFrame:
        """
        Batch prediction on a DataFrame.
        """
        df = patients_df.copy()
        if hasattr(self.pipeline, "predict_proba"):
            raw_probs = self.pipeline.predict_proba(df)
            classes = list(getattr(self.pipeline, "classes_", self.classes))
            d_idx = classes.index("Dengue") if "Dengue" in classes else self.dengue_index
            t_idx = 1 - d_idx if len(classes) == 2 else 0

            dengue_probs = raw_probs[:, d_idx]
            preds = [classes[d_idx] if p >= self.optimal_threshold else classes[t_idx] for p in dengue_probs]
            df["Predicted_Disease"] = preds
            for i, cls in enumerate(classes):
                df[f"Prob_{cls}"] = raw_probs[:, i].round(4)
        else:
            df["Predicted_Disease"] = self.pipeline.predict(df)

        return df
