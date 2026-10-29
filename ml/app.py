"""
Solar Vest ML Microservice
===========================
FastAPI app that serves the trained Keras model for predictions.
"""

import os
import sys

if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
import numpy as np
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import tensorflow as tf

from contextlib import asynccontextmanager

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "solar_model.keras")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "model", "scaler.pkl")

model = None
scaler = None


def do_load_model():
    global model, scaler
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        model = tf.keras.models.load_model(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        print("✅ Model and scaler loaded successfully")
    else:
        print("⚠️ Model not found. Run ml/model/train.py first.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    do_load_model()
    yield


app = FastAPI(
    title="☀️ Solar Vest ML Service",
    description="Predicts monthly solar energy generation (kWh)",
    version="1.0.0",
    lifespan=lifespan,
)

# Load eagerly on module import as well
do_load_model()


FEATURES = [
    "area_m2", "latitude", "longitude", "tilt_angle",
    "azimuth_angle", "panel_type_encoded", "num_panels",
    "month", "ghi", "temperature"
]


class PredictRequest(BaseModel):
    area_m2: float
    latitude: float
    longitude: float
    tilt_angle: float
    azimuth_angle: float
    panel_type_encoded: int   # 0=Mono, 1=Poly, 2=Thin-film
    num_panels: int
    month: int                # 1–12
    ghi: float                # Global Horizontal Irradiance kWh/m²/day
    temperature: float        # Avg temperature °C


class PredictResponse(BaseModel):
    monthly_kwh: float


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    if model is None or scaler is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Run training first: python ml/model/train.py"
        )
    features = np.array([[
        req.area_m2, req.latitude, req.longitude,
        req.tilt_angle, req.azimuth_angle, req.panel_type_encoded,
        req.num_panels, req.month, req.ghi, req.temperature
    ]])
    scaled = scaler.transform(features)
    prediction = model.predict(scaled, verbose=0).flatten()[0]
    return PredictResponse(monthly_kwh=round(float(max(0, prediction)), 2))


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "scaler_loaded": scaler is not None,
    }


@app.get("/")
def root():
    return {"service": "Solar Vest ML Service", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
