"""
Neorora - prediction function for the app.
Input:  a table of patient features (same 23 columns as features_train.csv)
Output: risk %, risk level (Low / Medium / High) and the top 3 reasons per patient.
"""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

MODEL_PATH = Path(__file__).resolve().parent / "models" / "model.joblib"
_bundle = joblib.load(MODEL_PATH)

MODEL = _bundle["model"]
THRESHOLD = _bundle["threshold"]          # 0.67
FEATURES = _bundle["features"]            # 23 input features, in order
SELECTED = _bundle["selected"]            # 15 features the model uses
REASONS = _bundle["reasons"]              # plain-language text for each feature


def _risk_level(p):
    if p >= THRESHOLD:
        return "High"
    if p >= 0.5:
        return "Medium"
    return "Low"


def predict(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")

    X = df[FEATURES]
    proba = MODEL.predict_proba(X)[:, 1]

    scaler = MODEL.named_steps["scale"]
    selector = MODEL.named_steps["select"]
    coef = MODEL.named_steps["model"].coef_[0]
    Z = selector.transform(scaler.transform(X))
    contrib = Z * coef

    rows = []
    for p, z_row, c_row in zip(proba, Z, contrib):
        top = np.argsort(c_row)[::-1][:3]
        reasons = []
        for i in top:
            high, low = REASONS.get(SELECTED[i], (SELECTED[i] + " high", SELECTED[i] + " low"))
            reasons.append(high if z_row[i] > 0 else low)
        rows.append({
            "risk_percent": round(float(p) * 100, 1),
            "risk_level": _risk_level(p),
            "reason_1": reasons[0], "reason_2": reasons[1], "reason_3": reasons[2],
        })

    out = pd.DataFrame(rows, index=df.index)
    if "patient" in df.columns:
        out.insert(0, "patient", df["patient"].values)
    return out


if __name__ == "__main__":
    # Quick test on 3 test patients
    root = Path(__file__).resolve().parent.parent
    sample = pd.read_csv(root / "data" / "processed" / "features_test.csv").head(3)
    print(predict(sample))