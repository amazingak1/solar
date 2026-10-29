import json
import threading
import paho.mqtt.client as mqtt
from datetime import datetime
from app.config import settings

_mqtt_client = None


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT Connected")
        client.subscribe("solar/+/data")
    else:
        print(f"❌ MQTT connection failed with code {rc}")


def on_message(client, userdata, msg):
    """Handle incoming sensor data and save to MongoDB."""
    try:
        payload = json.loads(msg.payload.decode())
        panel_id = payload.get("panel_id")
        if not panel_id:
            return

        # Import here to avoid circular imports
        import asyncio
        from app.database import get_db

        async def save():
            db = get_db()
            if db is None:
                return
            reading = {
                "panel_id": panel_id,
                "timestamp": datetime.utcnow(),
                "current_amps": payload.get("current_amps", 0),
                "voltage_volts": payload.get("voltage_volts", 0),
                "temperature_celsius": payload.get("temperature_celsius", 0),
                "irradiance_wm2": payload.get("irradiance_wm2", 0),
                "power_watts": payload.get("current_amps", 0) * payload.get("voltage_volts", 0),
            }
            await db.sensor_readings.insert_one(reading)

        loop = asyncio.new_event_loop()
        loop.run_until_complete(save())
        loop.close()

    except Exception as e:
        print(f"MQTT message error: {e}")


def start_mqtt_listener():
    global _mqtt_client
    try:
        _mqtt_client = mqtt.Client()
        _mqtt_client.on_connect = on_connect
        _mqtt_client.on_message = on_message
        _mqtt_client.connect(settings.mqtt_broker, settings.mqtt_port, 60)
        thread = threading.Thread(target=_mqtt_client.loop_forever, daemon=True)
        thread.start()
        print("🔌 MQTT listener started in background thread")
    except Exception as e:
        print(f"⚠️  MQTT not available (running without IoT): {e}")
