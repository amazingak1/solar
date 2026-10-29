"""
Dummy Data Generator for Solar Vest ML Model
=============================================
Generates 10,000 synthetic solar panel records using physics-based formulas.
Uses pure NumPy and standard libraries (no pandas required, avoiding Windows Smart App Control issues).

Formula:
  monthly_kwh = area_m2 × num_panels × panel_efficiency
                × GHI × days_in_month
                × tilt_factor × temp_factor
                + noise
"""

import os
import csv
import random
from math import cos, radians
import numpy as np

# Panel efficiency by type
PANEL_EFFICIENCY = {
    0: 0.20,  # Monocrystalline
    1: 0.17,  # Polycrystalline
    2: 0.12,  # Thin-film
}

# Monthly GHI (kWh/m²/day) and temperature per city
CITY_DATA = {
    "Delhi":     {"lat": 28.6, "lon": 77.2, "ghi": [3.5,4.5,5.8,6.5,7.0,6.5,5.5,5.2,5.8,5.5,4.2,3.2], "temp": [14,17,23,30,35,38,35,34,32,28,21,15]},
    "Mumbai":    {"lat": 19.0, "lon": 72.8, "ghi": [5.5,6.2,6.8,6.5,5.8,3.5,3.0,3.2,4.5,5.8,5.5,5.2], "temp": [24,25,27,30,32,30,28,28,29,30,28,25]},
    "Bangalore": {"lat": 12.9, "lon": 77.6, "ghi": [5.8,6.2,6.5,6.2,5.8,4.8,4.5,4.8,5.2,5.5,5.2,5.5], "temp": [21,23,26,28,27,24,23,24,24,24,22,21]},
    "Chennai":   {"lat": 13.0, "lon": 80.2, "ghi": [5.5,6.0,6.5,6.5,6.0,5.0,4.8,5.0,5.2,4.8,4.5,5.0], "temp": [26,28,30,32,35,36,35,35,34,32,29,27]},
    "Hyderabad": {"lat": 17.3, "lon": 78.4, "ghi": [5.5,6.0,6.5,6.5,6.5,5.0,4.5,4.8,5.2,5.5,5.0,5.2], "temp": [22,25,29,33,36,34,30,29,29,28,24,22]},
    "Kolkata":   {"lat": 22.5, "lon": 88.3, "ghi": [4.2,5.0,5.8,6.0,6.0,4.5,4.0,4.2,4.8,5.2,4.5,3.8], "temp": [19,22,28,32,34,33,31,31,31,29,25,20]},
    "Jaipur":    {"lat": 26.9, "lon": 75.8, "ghi": [4.0,5.0,6.2,7.0,7.5,7.0,6.0,5.8,6.0,5.8,4.5,3.8], "temp": [14,18,24,31,37,40,36,34,33,28,21,15]},
    "Ahmedabad": {"lat": 23.0, "lon": 72.6, "ghi": [4.5,5.5,6.5,7.0,7.5,7.0,5.5,5.5,6.0,6.0,5.0,4.2], "temp": [18,21,27,33,38,38,33,31,31,30,24,19]},
}

DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

FEATURES = [
    "area_m2", "latitude", "longitude", "tilt_angle",
    "azimuth_angle", "panel_type_encoded", "num_panels",
    "month", "ghi", "temperature"
]
TARGET = "monthly_kwh"


def tilt_factor(tilt_angle: float, latitude: float, month: int) -> float:
    declination = [-23.45, -17, -8, 4, 15, 23.45, 23.45, 15, 4, -8, -17, -23.45]
    dec = declination[month - 1]
    optimal_tilt = latitude - dec
    diff = abs(tilt_angle - optimal_tilt)
    return max(0.5, cos(radians(min(diff, 90))))


def temp_factor(temp_celsius: float) -> float:
    excess = max(0, temp_celsius - 25)
    return 1.0 - (0.004 * excess)


def generate_dataset(n_samples: int = 10000):
    """Generates synthetic dataset and returns (X, y) as numpy arrays."""
    cities = list(CITY_DATA.keys())
    X = np.zeros((n_samples, len(FEATURES)), dtype=np.float32)
    y = np.zeros((n_samples,), dtype=np.float32)

    for i in range(n_samples):
        city = random.choice(cities)
        city_info = CITY_DATA[city]
        month = random.randint(1, 12)
        area_m2 = round(random.uniform(1.0, 20.0), 2)
        num_panels = random.randint(1, 20)
        panel_type = random.randint(0, 2)
        tilt = round(random.uniform(0, 45), 1)
        azimuth = round(random.uniform(90, 270), 1)

        ghi = city_info["ghi"][month - 1]
        temp = city_info["temp"][month - 1]
        latitude = city_info["lat"]
        longitude = city_info["lon"]

        efficiency = PANEL_EFFICIENCY[panel_type]
        tf = tilt_factor(tilt, latitude, month)
        tmf = temp_factor(temp)
        days = DAYS_IN_MONTH[month - 1]

        az_diff = abs(azimuth - 180)
        az_factor = max(0.6, cos(radians(min(az_diff, 90))))

        monthly_kwh = (
            area_m2 * num_panels * efficiency
            * ghi * days
            * tf * tmf * az_factor
        )

        noise = random.gauss(1.0, 0.05)
        monthly_kwh = max(0.0, round(monthly_kwh * noise, 2))

        X[i] = [
            area_m2, latitude, longitude, tilt,
            azimuth, panel_type, num_panels,
            month, ghi, temp
        ]
        y[i] = monthly_kwh

    return X, y


def save_dataset_csv(filename: str, X: np.ndarray, y: np.ndarray):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(FEATURES + [TARGET])
        for i in range(len(y)):
            writer.writerow(list(X[i]) + [y[i]])


if __name__ == "__main__":
    X, y = generate_dataset(10000)
    save_dataset_csv("data/solar_dummy_data.csv", X, y)
    print(f"✅ Generated {len(y)} records. Average monthly kWh: {y.mean():.2f}")
