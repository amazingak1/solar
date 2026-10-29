from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SensorReading(BaseModel):
    panel_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    current_amps: float
    voltage_volts: float
    temperature_celsius: float
    irradiance_wm2: float
    power_watts: Optional[float] = None  # computed: current * voltage

    class Config:
        from_attributes = True


class SensorReadingOut(SensorReading):
    id: str


class ROIResult(BaseModel):
    panel_id: str
    monthly_kwh: float
    monthly_revenue_inr: float
    annual_revenue_inr: float
    payback_months: float
    payback_years: float
    roi_10yr_pct: float
    roi_25yr_pct: float
    break_even_month: int
    installation_cost: float
