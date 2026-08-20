from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.engine import Connection

from ..db import get_conn
from ..schemas import DeviceOut, SensorReadingOut
from ..util import default_date_range

router = APIRouter(tags=["devices"])


@router.get("/devices", response_model=list[DeviceOut])
def list_devices(conn: Connection = Depends(get_conn)) -> list[DeviceOut]:
    sql = """
        SELECT
            d.device_id, d.device_type, d.location, d.install_date, d.is_active,
            lr.reading_ts AS latest_reading_ts, lr.value AS latest_value,
            lr.metric_type, lr.unit
        FROM mart.dim_device d
        LEFT JOIN LATERAL (
            SELECT reading_ts, value, metric_type, unit
            FROM mart.fact_sensor_readings f
            WHERE f.device_key = d.device_key
            ORDER BY reading_ts DESC
            LIMIT 1
        ) lr ON true
        ORDER BY d.device_id
    """
    rows = conn.execute(text(sql)).mappings().all()
    return [DeviceOut(**row) for row in rows]


@router.get("/devices/{device_id}/readings", response_model=list[SensorReadingOut])
def device_readings(
    device_id: str,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    limit: int = Query(500, le=5000),
    conn: Connection = Depends(get_conn),
) -> list[SensorReadingOut]:
    if date_from is None or date_to is None:
        default_from, default_to = default_date_range()
        date_from = date_from or default_from
        date_to = date_to or default_to

    sql = """
        SELECT f.reading_id::text, dv.device_id, f.metric_type, f.value, f.unit, f.reading_ts, f.is_anomaly
        FROM mart.fact_sensor_readings f
        JOIN mart.dim_device dv ON dv.device_key = f.device_key
        JOIN mart.dim_date dd ON dd.date_key = f.date_key
        WHERE dv.device_id = :device_id AND dd.full_date BETWEEN :date_from AND :date_to
        ORDER BY f.reading_ts DESC
        LIMIT :limit
    """
    rows = conn.execute(
        text(sql),
        {"device_id": device_id, "date_from": date_from, "date_to": date_to, "limit": limit},
    ).mappings().all()
    return [SensorReadingOut(**row) for row in rows]


@router.get("/meta/devices", response_model=list[str])
def meta_devices(conn: Connection = Depends(get_conn)) -> list[str]:
    rows = conn.execute(
        text("SELECT device_id FROM mart.dim_device WHERE is_active ORDER BY device_id")
    ).scalars().all()
    return list(rows)
