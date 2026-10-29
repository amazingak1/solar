from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017/solar_vest"
    secret_key: str = "supersecretkey_change_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    ml_service_url: str = "http://localhost:8001"
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
