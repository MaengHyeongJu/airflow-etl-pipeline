from datetime import date, datetime

from pydantic import BaseModel


class KpiSummary(BaseModel):
    date_from: date
    date_to: date
    total_readings: int
    active_devices: int
    anomaly_count: int
    anomaly_rate_pct: float
    log_event_count: int
    error_log_count: int


class SensorTimeseriesPoint(BaseModel):
    full_date: date
    metric_type: str
    reading_count: int
    avg_value: float | None
    min_value: float | None
    max_value: float | None
    anomaly_count: int


class DeviceOut(BaseModel):
    device_id: str
    device_type: str
    location: str | None
    install_date: date | None
    is_active: bool
    latest_reading_ts: datetime | None
    latest_value: float | None
    metric_type: str | None
    unit: str | None


class SensorReadingOut(BaseModel):
    reading_id: str
    device_id: str
    metric_type: str
    value: float
    unit: str | None
    reading_ts: datetime
    is_anomaly: bool


class LogLevelSummary(BaseModel):
    level: str
    event_count: int


class LogEventOut(BaseModel):
    log_id: str
    service: str
    level: str
    message: str | None
    event_ts: datetime


class LogTimeseriesPoint(BaseModel):
    full_date: date
    level: str
    event_count: int
