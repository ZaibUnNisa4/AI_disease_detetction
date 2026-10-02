import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import config
from training.train_identification import train_svm_model


class DiseaseIdentifier:
    def __init__(self, model_path: Path = None):
        self.model_path = model_path or config.IDENTIFICATION_MODEL
        self.model = self._load_or_train()

    def _load_or_train(self):
        # 1. Check primary saved models path
        if self.model_path.exists():
            try:
                return joblib.load(self.model_path)
            except Exception as e:
                print(f"Notice: Primary model at {self.model_path} cannot be unpickled ({e}).")

        # 2. Check notebook location
        fallback = config.BASE_DIR / "identification" / "disease_identification_svm.pkl"
        if fallback.exists() and fallback != self.model_path:
            try:
                return joblib.load(fallback)
            except Exception:
                pass

        # 3. Train on the fly and persist
        print("Training fresh SVM model locally using available datasets...")
        return train_svm_model()

    def _clean_input(self, age: float, gender: str, fever_duration: float, skin_manifestation) -> pd.DataFrame:
        clean_gender = str(gender).strip().title()
        if clean_gender not in ["Male", "Female"]:
            # Default fallback to most common or keep string
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
        return pd.DataFrame(data)

    def predict_patient(self, age: float, gender: str, fever_duration: float, skin_manifestation) -> dict:
        """
        Predict whether patient symptoms correspond to Dengue or Typhoid.
        """
        input_df = self._clean_input(age, gender, fever_duration, skin_manifestation)
        pred_label = self.model.predict(input_df)[0]

        # Compute balanced probability estimates via decision boundary sigmoid
        probs = {}
        confidence = None
        if hasattr(self.model, "decision_function"):
            decision = float(self.model.decision_function(input_df)[0])
            classes = list(getattr(self.model, "classes_", ["Dengue", "Typhoid"]))
            p_class1 = 1.0 / (1.0 + np.exp(-decision))
            p_class0 = 1.0 - p_class1
            probs = {classes[0]: round(float(p_class0), 4), classes[1]: round(float(p_class1), 4)}
            confidence = probs.get(pred_label, round(float(max(p_class0, p_class1)), 4))
        elif hasattr(self.model, "predict_proba"):
            raw_probs = self.model.predict_proba(input_df)[0]
            classes = self.model.classes_
            probs = {cls: round(float(prob), 4) for cls, prob in zip(classes, raw_probs)}
            confidence = probs.get(pred_label, round(float(max(raw_probs)), 4))

        return {
            "predicted_disease": pred_label,
            "confidence": confidence,
            "probabilities": probs,
            "patient_features": {
                "age": float(age),
                "gender": input_df["Gender"].iloc[0],
                "fever_duration_days": float(fever_duration),
                "skin_manifestation": bool(input_df["Skin_Manifestation"].iloc[0])
            }
        }

    def predict_batch(self, patients_df: pd.DataFrame) -> pd.DataFrame:
        """
        Batch prediction on a DataFrame with columns ['Age', 'Gender', 'Fever_Duration', 'Skin_Manifestation'].
        """
        df = patients_df.copy()
        preds = self.model.predict(df)
        df["Predicted_Disease"] = preds

        if hasattr(self.model, "decision_function"):
            decisions = self.model.decision_function(df)
            classes = list(getattr(self.model, "classes_", ["Dengue", "Typhoid"]))
            p_class1 = 1.0 / (1.0 + np.exp(-decisions))
            p_class0 = 1.0 - p_class1
            df[f"Prob_{classes[0]}"] = np.round(p_class0, 4)
            df[f"Prob_{classes[1]}"] = np.round(p_class1, 4)
        elif hasattr(self.model, "predict_proba"):
            raw_probs = self.model.predict_proba(df)
            for i, cls in enumerate(self.model.classes_):
                df[f"Prob_{cls}"] = raw_probs[:, i].round(4)

        return df
