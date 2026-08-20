from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import devices, health, kpis, logs, sensors

app = FastAPI(title="ETL Portfolio Dashboard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(kpis.router, prefix="/api")
app.include_router(sensors.router, prefix="/api")
app.include_router(devices.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
