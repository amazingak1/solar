import sys
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import connect_db, close_db
from app.routers import auth, panels, sensors, predictions, investors
from app.services.mqtt_service import start_mqtt_listener


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    start_mqtt_listener()
    yield
    await close_db()


app = FastAPI(
    title="☀️ Solar Vest API",
    description="IoT + ML platform for solar panel monitoring and ROI prediction",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://solar-frontend-ctmc.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(panels.router)
app.include_router(sensors.router)
app.include_router(predictions.router)
app.include_router(investors.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "Solar Vest API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
