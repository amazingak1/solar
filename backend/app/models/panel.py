from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class PanelType(str, Enum):
    monocrystalline = "monocrystalline"
    polycrystalline = "polycrystalline"
    thin_film = "thin_film"


# Recommended tilt angles by city
CITY_DEFAULTS = {
    "Delhi":     {"latitude": 28.6, "longitude": 77.2, "tilt": 28},
    "Mumbai":    {"latitude": 19.0, "longitude": 72.8, "tilt": 19},
    "Bangalore": {"latitude": 12.9, "longitude": 77.6, "tilt": 13},
    "Chennai":   {"latitude": 13.0, "longitude": 80.2, "tilt": 13},
    "Hyderabad": {"latitude": 17.3, "longitude": 78.4, "tilt": 17},
    "Kolkata":   {"latitude": 22.5, "longitude": 88.3, "tilt": 22},
    "Jaipur":    {"latitude": 26.9, "longitude": 75.8, "tilt": 27},
    "Ahmedabad": {"latitude": 23.0, "longitude": 72.6, "tilt": 23},
}


class PanelCreate(BaseModel):
    name: str
    city: str = "Delhi"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_m2: float = Field(..., gt=0, description="Area of each panel in m²")
    num_panels: int = Field(..., gt=0)
    tilt_angle: float = Field(..., ge=0, le=90)
    azimuth_angle: float = Field(180.0, ge=0, le=360, description="180=South (optimal in India)")
    panel_type: PanelType = PanelType.monocrystalline
    installation_cost: float = Field(..., gt=0, description="Total install cost in ₹")


class PanelOut(BaseModel):
    id: str
    name: str
    city: str
    latitude: float
    longitude: float
    area_m2: float
    num_panels: int
    tilt_angle: float
    azimuth_angle: float
    panel_type: PanelType
    installation_cost: float
    owner_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class PanelUpdate(BaseModel):
    name: Optional[str] = None
    tilt_angle: Optional[float] = None
    azimuth_angle: Optional[float] = None
    installation_cost: Optional[float] = None
