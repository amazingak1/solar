from fastapi import APIRouter, HTTPException, Depends, Query
from app.database import get_db
from app.services.auth_service import get_current_user
from datetime import datetime, timezone
import math
import random

router = APIRouter(prefix="/sensors", tags=["Sensors"])

CITY_IRRADIANCE = {
    "Delhi":     [250, 350, 500, 600, 650, 600, 500, 480, 530, 500, 380, 280],
    "Mumbai":    [500, 560, 620, 590, 520, 300, 260, 280, 400, 520, 490, 460],
    "Bangalore": [530, 560, 590, 560, 520, 420, 400, 420, 470, 490, 460, 490],
    "Chennai":   [500, 540, 590, 590, 540, 450, 430, 450, 470, 430, 400, 450],
    "Hyderabad": [500, 540, 590, 590, 590, 450, 400, 430, 470, 490, 450, 460],
    "Kolkata":   [380, 450, 520, 540, 540, 400, 360, 380, 430, 460, 400, 340],
    "Jaipur":    [360, 450, 560, 630, 680, 630, 540, 520, 540, 520, 400, 340],
    "Ahmedabad": [400, 490, 590, 630, 680, 630, 490, 490, 540, 540, 450, 380],
}
CITY_TEMP = {
    "Delhi":     [14, 17, 23, 30, 35, 38, 35, 34, 32, 28, 21, 15],
    "Mumbai":    [24, 25, 27, 30, 32, 30, 28, 28, 29, 30, 28, 25],
    "Bangalore": [21, 23, 26, 28, 27, 24, 23, 24, 24, 24, 22, 21],
    "Chennai":   [26, 28, 30, 32, 35, 36, 35, 35, 34, 32, 29, 27],
    "Hyderabad": [22, 25, 29, 33, 36, 34, 30, 29, 29, 28, 24, 22],
    "Kolkata":   [19, 22, 28, 32, 34, 33, 31, 31, 31, 29, 25, 20],
    "Jaipur":    [14, 18, 24, 31, 37, 40, 36, 34, 33, 28, 21, 15],
    "Ahmedabad": [18, 21, 27, 33, 38, 38, 33, 31, 31, 30, 24, 19],
}


def simulate_reading(panel: dict) -> dict:
    """Generate a realistic simulated sensor reading for a panel."""
    city = panel.get("city", "Delhi")
    month = datetime.now().month - 1
    irr_base = CITY_IRRADIANCE.get(city, CITY_IRRADIANCE["Delhi"])[month]
    temp_base = CITY_TEMP.get(city, CITY_TEMP["Delhi"])[month]

    hour = datetime.now().hour
    tod_factor = max(0, math.sin(math.pi * (hour - 6) / 12)) if 6 <= hour <= 18 else 0.0

    # Cloud cover variation
    cloud_roll = random.random()
    if cloud_roll < 0.05:
        cloud_factor = random.uniform(0.15, 0.35)
    elif cloud_roll < 0.20:
        cloud_factor = random.uniform(0.55, 0.78)
    else:
        cloud_factor = random.uniform(0.91, 1.09)

    irradiance = round(irr_base * tod_factor * cloud_factor, 1)
    temp = round(temp_base + random.uniform(-3, 4) + (irradiance / 1000) * 8, 1)

    panel_eff = {"monocrystalline": 0.20, "polycrystalline": 0.17, "thin_film": 0.12}.get(
        panel.get("panel_type", "monocrystalline"), 0.18
    )
    degradation = random.uniform(0.995, 1.005)
    power_w = round(panel.get("area_m2", 2) * panel.get("num_panels", 10) * panel_eff * (irradiance / 1000) * degradation * 1000, 1)
    voltage = round(random.uniform(34.5, 41.5) - (temp - 25) * 0.04, 1)
    voltage = max(30.0, voltage)
    current = round(power_w / voltage, 2) if voltage > 0 else 0.0

    return {
        "panel_id": panel.get("id", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "current_amps": max(0.0, current),
        "voltage_volts": voltage,
        "temperature_celsius": temp,
        "irradiance_wm2": max(0.0, irradiance),
        "power_watts": max(0.0, power_w),
        "simulated": True,
    }


@router.get("/{panel_id}/live")
async def get_live_reading(panel_id: str, current_user: dict = Depends(get_current_user)):
    """Get the most recent sensor reading. Falls back to physics-based simulation."""
    db = get_db()

    reading = await db.sensor_readings.find_one(
        {"panel_id": panel_id},
        sort=[("timestamp", -1)]
    )
    if reading:
        return reading

    panel = await db.panels.find_one({"id": panel_id})
    if not panel:
        panel = {"city": "Delhi", "area_m2": 2, "num_panels": 10, "panel_type": "monocrystalline", "id": panel_id}
    return simulate_reading(panel)


@router.get("/{panel_id}/history")
async def get_reading_history(
    panel_id: str,
    limit: int = Query(50, le=500),
    skip: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """Get paginated historical readings. Returns simulated history if none exist."""
    db = get_db()
    cursor = db.sensor_readings.find({"panel_id": panel_id}, sort=[("timestamp", -1)])
    readings = await cursor.skip(skip).limit(limit).to_list(limit)

    if not readings:
        panel = await db.panels.find_one({"id": panel_id})
        if not panel:
            panel = {"city": "Delhi", "area_m2": 2, "num_panels": 10, "panel_type": "monocrystalline", "id": panel_id}
        from datetime import timedelta
        history = []
        now = datetime.now(timezone.utc)
        for hrs_ago in range(min(limit, 168)):
            past_hour = (now - timedelta(hours=hrs_ago)).hour
            entry = simulate_reading(panel)
            entry["timestamp"] = (now - timedelta(hours=hrs_ago)).isoformat()
            history.append(entry)
        return history

    return readings


@router.post("/ingest", status_code=201)
async def ingest_reading(reading: dict):
    """Ingest a sensor reading (MQTT or direct POST)."""
    db = get_db()
    reading["timestamp"] = datetime.utcnow().isoformat()
    if "current_amps" in reading and "voltage_volts" in reading:
        reading["power_watts"] = reading["current_amps"] * reading["voltage_volts"]
    result = await db.sensor_readings.insert_one(reading)
    return {"id": result.inserted_id, "status": "saved"}
