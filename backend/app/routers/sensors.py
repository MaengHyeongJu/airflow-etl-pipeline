from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.engine import Connection

from ..db import get_conn
from ..schemas import SensorReadingOut, SensorTimeseriesPoint
from ..util import date_key, default_date_range

router = APIRouter(tags=["sensors"])


@router.get("/sensors/timeseries", response_model=list[SensorTimeseriesPoint])
def sensor_timeseries(
    metric_type: str | None = Query(None),
    device_id: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    conn: Connection = Depends(get_conn),
) -> list[SensorTimeseriesPoint]:
    if date_from is None or date_to is None:
        default_from, default_to = default_date_range()
        date_from = date_from or default_from
        date_to = date_to or default_to

    sql = """
        SELECT
            dd.full_date,
            a.metric_type,
            SUM(a.reading_count) AS reading_count,
            AVG(a.avg_value) AS avg_value,
            MIN(a.min_value) AS min_value,
            MAX(a.max_value) AS max_value,
            SUM(a.anomaly_count) AS anomaly_count
        FROM mart.agg_daily_device_metrics a
        JOIN mart.dim_date dd ON dd.date_key = a.date_key
        JOIN mart.dim_device dv ON dv.device_key = a.device_key
        WHERE a.date_key BETWEEN :dk_from AND :dk_to
    """
    params = {"dk_from": date_key(date_from), "dk_to": date_key(date_to)}
    if metric_type:
        sql += " AND a.metric_type = :metric_type"
        params["metric_type"] = metric_type
    if device_id:
        sql += " AND dv.device_id = :device_id"
        params["device_id"] = device_id
    sql += " GROUP BY dd.full_date, a.metric_type ORDER BY dd.full_date"

    rows = conn.execute(text(sql), params).mappings().all()
    return [SensorTimeseriesPoint(**row) for row in rows]


@router.get("/sensors/anomalies/recent", response_model=list[SensorReadingOut])
def recent_anomalies(
    limit: int = Query(50, le=500),
    conn: Connection = Depends(get_conn),
) -> list[SensorReadingOut]:
    sql = """
        SELECT f.reading_id::text, dv.device_id, f.metric_type, f.value, f.unit, f.reading_ts, f.is_anomaly
        FROM mart.fact_sensor_readings f
        JOIN mart.dim_device dv ON dv.device_key = f.device_key
        WHERE f.is_anomaly = true
        ORDER BY f.reading_ts DESC
        LIMIT :limit
    """
    rows = conn.execute(text(sql), {"limit": limit}).mappings().all()
    return [SensorReadingOut(**row) for row in rows]
