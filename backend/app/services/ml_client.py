import os
import httpx
from app.config import settings

_local_model = None
_local_scaler = None


def _get_local_inference(payload: dict) -> dict:
    """Fallback in-process inference if ML microservice is not running."""
    global _local_model, _local_scaler
    if _local_model is None:
        import joblib
        import tensorflow as tf

        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.normpath(os.path.join(base_dir, "..", "..", "..", "ml", "model", "solar_model.keras"))
        scaler_path = os.path.normpath(os.path.join(base_dir, "..", "..", "..", "ml", "model", "scaler.pkl"))

        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Model artifacts not found at {model_path}")

        _local_model = tf.keras.models.load_model(model_path)
        _local_scaler = joblib.load(scaler_path)

    import numpy as np

    features = np.array([[
        payload["area_m2"],
        payload["latitude"],
        payload["longitude"],
        payload["tilt_angle"],
        payload["azimuth_angle"],
        payload["panel_type_encoded"],
        payload["num_panels"],
        payload["month"],
        payload["ghi"],
        payload["temperature"],
    ]])
    scaled = _local_scaler.transform(features)
    pred = _local_model.predict(scaled, verbose=0).flatten()[0]
    return {"monthly_kwh": round(float(max(0, pred)), 2)}


async def get_ml_prediction(payload: dict) -> dict:
    """
    Attempts to call the dedicated ML microservice.
    If unavailable, falls back automatically to local in-process inference.
    """
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(
                f"{settings.ml_service_url}/predict",
                json=payload
            )
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass

    return _get_local_inference(payload)


def calculate_roi(monthly_kwh: float, installation_cost: float) -> dict:
    """
    Deterministic ROI calculator based on predicted monthly kWh.
    Assumes ₹7/kWh tariff, 25-year lifespan, factoring in ~0.6% annual
    degradation and ~2.5% tariff escalation.
    """
    tariff = 7.0  # ₹ per kWh
    monthly_revenue = monthly_kwh * tariff
    annual_revenue = monthly_revenue * 12

    payback_months = installation_cost / monthly_revenue if monthly_revenue > 0 else float("inf")
    payback_years = payback_months / 12

    # Compounding lifetime return with solar degradation and tariff inflation
    cum_10yr = sum(annual_revenue * ((1 - 0.006) ** yr) * ((1 + 0.025) ** yr) for yr in range(10))
    cum_25yr = sum(annual_revenue * ((1 - 0.006) ** yr) * ((1 + 0.025) ** yr) for yr in range(25))

    roi_10yr = ((cum_10yr - installation_cost) / installation_cost) * 100 if installation_cost > 0 else 0
    roi_25yr = ((cum_25yr - installation_cost) / installation_cost) * 100 if installation_cost > 0 else 0

    break_even_month = int(payback_months) + 1 if monthly_revenue > 0 else -1

    return {
        "monthly_kwh": round(monthly_kwh, 2),
        "monthly_revenue_inr": round(monthly_revenue, 2),
        "annual_revenue_inr": round(annual_revenue, 2),
        "payback_months": round(payback_months, 1),
        "payback_years": round(payback_years, 2),
        "roi_10yr_pct": round(roi_10yr, 1),
        "roi_25yr_pct": round(roi_25yr, 1),
        "break_even_month": break_even_month,
        "installation_cost": installation_cost,
    }
