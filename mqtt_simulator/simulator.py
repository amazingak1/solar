"""
Solar Vest - MQTT IoT Sensor Simulator
========================================
Simulates real-time sensor data from solar panels.
Publishes to topic: solar/{panel_id}/data every 5 seconds.

Usage:
  python simulator.py --broker localhost --port 1883 --panels panel1,panel2
"""

import json
import time
import random
import argparse
import math
from datetime import datetime
import paho.mqtt.client as mqtt


def generate_reading(panel_id: str, base_irradiance: float = 800) -> dict:
    """
    Simulate realistic sensor readings for a solar panel.
    Values fluctuate slightly around realistic operating ranges.
    """
    hour = datetime.utcnow().hour
    # Simulate day/night cycle: irradiance peaks at midday
    time_factor = max(0, math.sin(math.pi * (hour - 6) / 12)) if 6 <= hour <= 18 else 0

    irradiance = round(base_irradiance * time_factor * random.uniform(0.9, 1.1), 1)
    temperature = round(25 + (irradiance / 100) * random.uniform(0.8, 1.2), 1)
    voltage = round(random.uniform(45.0, 52.0), 2)
    current = round((irradiance / 1000) * random.uniform(7.5, 9.5), 2)
    power = round(current * voltage, 2)

    return {
        "panel_id": panel_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "current_amps": current,
        "voltage_volts": voltage,
        "temperature_celsius": temperature,
        "irradiance_wm2": irradiance,
        "power_watts": power,
    }


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected to MQTT broker")
    else:
        print(f"❌ Connection failed with code {rc}")


def run_simulator(broker: str, port: int, panel_ids: list, interval: int = 5):
    client = mqtt.Client()
    client.on_connect = on_connect

    print(f"🔌 Connecting to MQTT broker at {broker}:{port}...")
    client.connect(broker, port, 60)
    client.loop_start()

    print(f"📡 Simulating {len(panel_ids)} panels: {panel_ids}")
    print(f"⏱  Publishing every {interval} seconds. Press Ctrl+C to stop.\n")

    try:
        while True:
            for panel_id in panel_ids:
                reading = generate_reading(panel_id)
                topic = f"solar/{panel_id}/data"
                payload = json.dumps(reading)
                client.publish(topic, payload, qos=1)
                print(f"📤 [{panel_id}] {reading['timestamp']} | "
                      f"Power: {reading['power_watts']}W | "
                      f"Irr: {reading['irradiance_wm2']} W/m² | "
                      f"Temp: {reading['temperature_celsius']}°C")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n🛑 Simulator stopped.")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solar Vest MQTT Simulator")
    parser.add_argument("--broker", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--panels", default="panel_001,panel_002,panel_003",
                        help="Comma-separated panel IDs")
    parser.add_argument("--interval", type=int, default=5,
                        help="Seconds between publishes")
    args = parser.parse_args()

    panel_ids = [p.strip() for p in args.panels.split(",")]
    run_simulator(args.broker, args.port, panel_ids, args.interval)
