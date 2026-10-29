from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db
from app.services.auth_service import get_current_user
from app.services.ml_client import get_ml_prediction, calculate_roi
from app.models.panel import CITY_DEFAULTS
from datetime import datetime
import random

router = APIRouter(prefix="/predict", tags=["Predictions"])

CITY_MONTHLY_DATA = {
    "Delhi":     {"ghi": [3.5,4.5,5.8,6.5,7.0,6.5,5.5,5.2,5.8,5.5,4.2,3.2], "temp": [14,17,23,30,35,38,35,34,32,28,21,15]},
    "Mumbai":    {"ghi": [5.5,6.2,6.8,6.5,5.8,3.5,3.0,3.2,4.5,5.8,5.5,5.2], "temp": [24,25,27,30,32,30,28,28,29,30,28,25]},
    "Bangalore": {"ghi": [5.8,6.2,6.5,6.2,5.8,4.8,4.5,4.8,5.2,5.5,5.2,5.5], "temp": [21,23,26,28,27,24,23,24,24,24,22,21]},
    "Chennai":   {"ghi": [5.5,6.0,6.5,6.5,6.0,5.0,4.8,5.0,5.2,4.8,4.5,5.0], "temp": [26,28,30,32,35,36,35,35,34,32,29,27]},
    "Hyderabad": {"ghi": [5.5,6.0,6.5,6.5,6.5,5.0,4.5,4.8,5.2,5.5,5.0,5.2], "temp": [22,25,29,33,36,34,30,29,29,28,24,22]},
    "Kolkata":   {"ghi": [4.2,5.0,5.8,6.0,6.0,4.5,4.0,4.2,4.8,5.2,4.5,3.8], "temp": [19,22,28,32,34,33,31,31,31,29,25,20]},
    "Jaipur":    {"ghi": [4.0,5.0,6.2,7.0,7.5,7.0,6.0,5.8,6.0,5.8,4.5,3.8], "temp": [14,18,24,31,37,40,36,34,33,28,21,15]},
    "Ahmedabad": {"ghi": [4.5,5.5,6.5,7.0,7.5,7.0,5.5,5.5,6.0,6.0,5.0,4.2], "temp": [18,21,27,33,38,38,33,31,31,30,24,19]},
}


def _build_payload(panel: dict, month: int, city_data: dict) -> dict:
    idx = month - 1
    panel_type_map = {"monocrystalline": 0, "polycrystalline": 1, "thin_film": 2}
    return {
        "area_m2": panel["area_m2"],
        "latitude": panel["latitude"],
        "longitude": panel["longitude"],
        "tilt_angle": panel["tilt_angle"],
        "azimuth_angle": panel["azimuth_angle"],
        "panel_type_encoded": panel_type_map.get(panel["panel_type"], 0),
        "num_panels": panel["num_panels"],
        "month": month,
        "ghi": city_data["ghi"][idx],
        "temperature": city_data["temp"][idx],
    }


@router.post("/")
async def predict(
    panel_id: str,
    month: int = datetime.utcnow().month,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    panel = await db.panels.find_one({"id": panel_id})
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    city_data = CITY_MONTHLY_DATA.get(panel["city"], CITY_MONTHLY_DATA["Delhi"])
    payload = _build_payload(panel, month, city_data)

    ml_result = await get_ml_prediction(payload)
    monthly_kwh = ml_result["monthly_kwh"]
    roi = calculate_roi(monthly_kwh, panel["installation_cost"])

    await db.predictions.insert_one({
        "panel_id": panel_id,
        "month": month,
        "monthly_kwh": monthly_kwh,
        "roi": roi,
        "created_at": datetime.utcnow(),
    })

    return {"panel_id": panel_id, "month": month, **roi}


@router.get("/{panel_id}/monthly")
async def monthly_forecast(panel_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    panel = await db.panels.find_one({"id": panel_id})
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    city_data = CITY_MONTHLY_DATA.get(panel["city"], CITY_MONTHLY_DATA["Delhi"])
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    forecast = []

    for i in range(12):
        payload = _build_payload(panel, i + 1, city_data)
        result = await get_ml_prediction(payload)
        noise = random.uniform(0.93, 1.07)
        kwh = round(result["monthly_kwh"] * noise, 1)
        forecast.append({"month": months[i], "monthly_kwh": kwh})

    return {"panel_id": panel_id, "city": panel["city"], "forecast": forecast}


@router.get("/{panel_id}/roi")
async def get_roi(panel_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    panel = await db.panels.find_one({"id": panel_id})
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    city_data = CITY_MONTHLY_DATA.get(panel["city"], CITY_MONTHLY_DATA["Delhi"])
    avg_ghi = sum(city_data["ghi"]) / 12
    avg_temp = sum(city_data["temp"]) / 12

    payload = {
        "area_m2": panel["area_m2"],
        "latitude": panel["latitude"],
        "longitude": panel["longitude"],
        "tilt_angle": panel["tilt_angle"],
        "azimuth_angle": panel["azimuth_angle"],
        "panel_type_encoded": {"monocrystalline": 0, "polycrystalline": 1, "thin_film": 2}.get(panel["panel_type"], 0),
        "num_panels": panel["num_panels"],
        "month": 6,
        "ghi": avg_ghi,
        "temperature": avg_temp,
    }

    ml_result = await get_ml_prediction(payload)
    roi = calculate_roi(ml_result["monthly_kwh"], panel["installation_cost"])
    return {"panel_id": panel_id, **roi}
