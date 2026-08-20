"""Idempotent partition-overwrite loads into the staging schema.

Each load deletes any existing rows for the partition (`dt = ds`) before
inserting, so re-running or backfilling a day is always safe.
"""
from __future__ import annotations

import logging

import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook

from generator.devices import DEVICES

logger = logging.getLogger(__name__)

CONN_ID = "datamart_postgres"


def upsert_dim_device() -> int:
    """Upsert the static device registry into mart.dim_device.

    Independent of any day's readings, so device metadata exists even before
    a device's first reading is loaded.
    """
    hook = PostgresHook(postgres_conn_id=CONN_ID)
    sql = """
        INSERT INTO mart.dim_device (device_id, device_type, location, install_date, is_active, updated_at)
        VALUES (%(device_id)s, %(device_type)s, %(location)s, %(install_date)s, TRUE, now())
        ON CONFLICT (device_id) DO UPDATE SET
            device_type = EXCLUDED.device_type,
            location = EXCLUDED.location,
            install_date = EXCLUDED.install_date,
            is_active = EXCLUDED.is_active,
            updated_at = now()
    """
    for device in DEVICES:
        hook.run(
            sql,
            parameters={
                "device_id": device.device_id,
                "device_type": device.device_type,
                "location": device.location,
                "install_date": device.install_date,
            },
        )
    logger.info("upsert_dim_device: upserted %d devices", len(DEVICES))
    return len(DEVICES)


def load_staging_sensor_readings(staging_path: str, ds: str) -> int:
    df = pd.read_parquet(staging_path)
    hook = PostgresHook(postgres_conn_id=CONN_ID)

    hook.run("DELETE FROM staging.sensor_readings_raw WHERE dt = %(ds)s", parameters={"ds": ds})

    if df.empty:
        logger.info("load_staging_sensor_readings ds=%s: nothing to load", ds)
        return 0

    rows = [
        (
            str(r.reading_id),
            str(r.device_id),
            str(r.metric_type),
            float(r.value),
            str(r.unit) if pd.notna(r.unit) else None,
            r.reading_ts.to_pydatetime(),
            bool(r.is_anomaly),
            ds,
        )
        for r in df.itertuples(index=False)
    ]
    hook.insert_rows(
        table="staging.sensor_readings_raw",
        rows=rows,
        target_fields=["reading_id", "device_id", "metric_type", "value", "unit", "reading_ts", "is_anomaly", "dt"],
        commit_every=1000,
    )
    logger.info("load_staging_sensor_readings ds=%s loaded=%d", ds, len(rows))
    return len(rows)


def load_staging_log_events(staging_path: str, ds: str) -> int:
    df = pd.read_parquet(staging_path)
    hook = PostgresHook(postgres_conn_id=CONN_ID)

    hook.run("DELETE FROM staging.log_events_raw WHERE dt = %(ds)s", parameters={"ds": ds})

    if df.empty:
        logger.info("load_staging_log_events ds=%s: nothing to load", ds)
        return 0

    rows = [
        (
            str(r.log_id),
            str(r.service),
            str(r.level),
            str(r.message) if pd.notna(r.message) else None,
            r.event_ts.to_pydatetime(),
            ds,
        )
        for r in df.itertuples(index=False)
    ]
    hook.insert_rows(
        table="staging.log_events_raw",
        rows=rows,
        target_fields=["log_id", "service", "level", "message", "event_ts", "dt"],
        commit_every=1000,
    )
    logger.info("load_staging_log_events ds=%s loaded=%d", ds, len(rows))
    return len(rows)
