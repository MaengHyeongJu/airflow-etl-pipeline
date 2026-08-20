from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.engine import Connection

from ..db import get_conn
from ..schemas import KpiSummary
from ..util import date_key, default_date_range

router = APIRouter(tags=["kpis"])


@router.get("/kpis/summary", response_model=KpiSummary)
def kpi_summary(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    conn: Connection = Depends(get_conn),
) -> KpiSummary:
    if date_from is None or date_to is None:
        default_from, default_to = default_date_range()
        date_from = date_from or default_from
        date_to = date_to or default_to

    dk_from, dk_to = date_key(date_from), date_key(date_to)

    readings_row = conn.execute(
        text(
            """
            SELECT
                COALESCE(SUM(reading_count), 0) AS total_readings,
                COALESCE(SUM(anomaly_count), 0) AS anomaly_count,
                COUNT(DISTINCT device_key) AS active_devices
            FROM mart.agg_daily_device_metrics
            WHERE date_key BETWEEN :dk_from AND :dk_to
            """
        ),
        {"dk_from": dk_from, "dk_to": dk_to},
    ).mappings().one()

    logs_row = conn.execute(
        text(
            """
            SELECT
                COALESCE(SUM(event_count), 0) AS log_event_count,
                COALESCE(SUM(event_count) FILTER (WHERE level IN ('ERROR', 'CRITICAL')), 0) AS error_log_count
            FROM mart.agg_daily_log_summary
            WHERE date_key BETWEEN :dk_from AND :dk_to
            """
        ),
        {"dk_from": dk_from, "dk_to": dk_to},
    ).mappings().one()

    total_readings = readings_row["total_readings"]
    anomaly_count = readings_row["anomaly_count"]
    anomaly_rate_pct = round((anomaly_count / total_readings * 100), 2) if total_readings else 0.0

    return KpiSummary(
        date_from=date_from,
        date_to=date_to,
        total_readings=total_readings,
        active_devices=readings_row["active_devices"],
        anomaly_count=anomaly_count,
        anomaly_rate_pct=anomaly_rate_pct,
        log_event_count=logs_row["log_event_count"],
        error_log_count=logs_row["error_log_count"],
    )
