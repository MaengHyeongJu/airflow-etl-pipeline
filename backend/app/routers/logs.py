from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.engine import Connection

from ..db import get_conn
from ..schemas import LogEventOut, LogLevelSummary, LogTimeseriesPoint
from ..util import date_key, default_date_range

router = APIRouter(tags=["logs"])


@router.get("/logs/summary", response_model=list[LogLevelSummary])
def logs_summary(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    conn: Connection = Depends(get_conn),
) -> list[LogLevelSummary]:
    if date_from is None or date_to is None:
        default_from, default_to = default_date_range()
        date_from = date_from or default_from
        date_to = date_to or default_to

    rows = conn.execute(
        text(
            """
            SELECT level, SUM(event_count) AS event_count
            FROM mart.agg_daily_log_summary
            WHERE date_key BETWEEN :dk_from AND :dk_to
            GROUP BY level
            ORDER BY level
            """
        ),
        {"dk_from": date_key(date_from), "dk_to": date_key(date_to)},
    ).mappings().all()
    return [LogLevelSummary(**row) for row in rows]


@router.get("/logs/recent", response_model=list[LogEventOut])
def logs_recent(
    level: str | None = Query(None),
    service: str | None = Query(None),
    limit: int = Query(200, le=2000),
    conn: Connection = Depends(get_conn),
) -> list[LogEventOut]:
    sql = """
        SELECT log_id::text, service, level, message, event_ts
        FROM mart.fact_log_events
        WHERE (:level IS NULL OR level = :level)
          AND (:service IS NULL OR service = :service)
        ORDER BY event_ts DESC
        LIMIT :limit
    """
    rows = conn.execute(text(sql), {"level": level, "service": service, "limit": limit}).mappings().all()
    return [LogEventOut(**row) for row in rows]


@router.get("/logs/timeseries", response_model=list[LogTimeseriesPoint])
def logs_timeseries(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    conn: Connection = Depends(get_conn),
) -> list[LogTimeseriesPoint]:
    if date_from is None or date_to is None:
        default_from, default_to = default_date_range()
        date_from = date_from or default_from
        date_to = date_to or default_to

    rows = conn.execute(
        text(
            """
            SELECT dd.full_date, a.level, SUM(a.event_count) AS event_count
            FROM mart.agg_daily_log_summary a
            JOIN mart.dim_date dd ON dd.date_key = a.date_key
            WHERE a.date_key BETWEEN :dk_from AND :dk_to
            GROUP BY dd.full_date, a.level
            ORDER BY dd.full_date
            """
        ),
        {"dk_from": date_key(date_from), "dk_to": date_key(date_to)},
    ).mappings().all()
    return [LogTimeseriesPoint(**row) for row in rows]


@router.get("/meta/services", response_model=list[str])
def meta_services(conn: Connection = Depends(get_conn)) -> list[str]:
    rows = conn.execute(text("SELECT DISTINCT service FROM mart.fact_log_events ORDER BY service")).scalars().all()
    return list(rows)
