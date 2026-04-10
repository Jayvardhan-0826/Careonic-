import os
import numpy as np
import joblib
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import tensorflow as tf

# ── paths relative to this file ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
MODEL_PATH  = BASE_DIR / "lstm_vitals_model.h5"
SCALER_PATH = BASE_DIR / "scaler.save"

# ── MongoDB config  (override via env vars) ───────────────────────────────────
MONGO_URI  = os.getenv("MONGO_URI", "mongodb+srv://cluster2024:cluster2024@cluster2024.8qmtq.mongodb.net/?appName=cluster2024")
DB_NAME    = os.getenv("DB_NAME",   "users_vital_data")

# ── load model & scaler once at startup ──────────────────────────────────────
print("Loading LSTM model …")
model  = tf.keras.models.load_model(str(MODEL_PATH), compile=False)
print("Loading scaler …")
scaler = joblib.load(str(SCALER_PATH))
print("Ready.")

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="Patient Vitals Predictor", version="1.0.0")

@app.get("/predict/{patient_id}")
def predict_vitals(patient_id: str):
    """
    Fetches the most-recent 12 vitals for *patient_id* from MongoDB,
    runs the LSTM model, and returns the next-12 predicted values
    for both glucose and heart_rate.
    """

    # 1. Connect and fetch last 12 records from patient's own collection
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db     = client[DB_NAME]
        col    = db[patient_id]          # collection name == patient_id

        # sort descending → grab 12 → reverse to restore chronological order
        cursor = (
            col.find(
                {},
                {"_id": 0, "glucose": 1, "heart_rate": 1, "time_stamp": 1}
            )
            .sort("time_stamp", -1)      # newest first
            .limit(12)
        )
        records = list(cursor)[::-1]     # flip back to oldest → newest
        client.close()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB error: {exc}")

    # 2. Validate we have enough data
    if len(records) < 12:
        raise HTTPException(
            status_code=422,
            detail=f"Patient '{patient_id}' has only {len(records)} vitals records; "
                   "need at least 12."
        )

    # records already contains exactly the last 12 rows in chronological order
    last_12 = records

    # 3. Build input array  [glucose, heart_rate]  — matches training order
    try:
        input_seq = np.array(
            [[r["glucose"], r["heart_rate"]] for r in last_12],
            dtype=np.float32
        )  # shape (12, 2)
    except KeyError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Missing field in vitals record: {e}"
        )

    # 4. Scale → reshape → predict → inverse-scale
    input_scaled = scaler.transform(input_seq)            # (12, 2)
    input_scaled = np.expand_dims(input_scaled, axis=0)   # (1, 12, 2)

    pred_scaled  = model.predict(input_scaled)[0]         # (12, 2)
    pred_real    = scaler.inverse_transform(pred_scaled)  # (12, 2)

    # 5. Build response
    predictions = [
        {
            "step":              i + 1,
            "minutes_ahead":    (i + 1) * 5,
            "predicted_glucose":    round(float(pred_real[i, 0]), 4),
            "predicted_heart_rate": round(float(pred_real[i, 1]), 4),
        }
        for i in range(12)
    ]

    return {
        "patient_id":  patient_id,
        "predictions": predictions
    }


# ── dev runner ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
