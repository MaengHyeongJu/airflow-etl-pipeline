"""Hand-rolled data-quality assertions run after the mart is built for a partition.

Kept simple and explicit (rather than a full DQ framework) so failures are
easy to read straight out of the task log. Raises AirflowException, which
fails the task and the DAG run, on any violation.
"""
from __future__ import annotations

import logging

from airflow.exceptions import AirflowException
from airflow.providers.postgres.hooks.postgres import PostgresHook

logger = logging.getLogger(__name__)

CONN_ID = "datamart_postgres"


def _date_key(ds: str) -> int:
    return int(ds.replace("-", ""))


def run_data_quality_checks(ds: str) -> None:
    hook = PostgresHook(postgres_conn_id=CONN_ID)
    date_key = _date_key(ds)
    failures: list[str] = []

    reading_count = hook.get_first(
        "SELECT count(*) FROM mart.fact_sensor_readings WHERE date_key = %(dk)s", parameters={"dk": date_key}
    )[0]
    if reading_count == 0:
        failures.append(f"fact_sensor_readings has 0 rows for date_key={date_key}")

    event_count = hook.get_first(
        "SELECT count(*) FROM mart.fact_log_events WHERE date_key = %(dk)s", parameters={"dk": date_key}
    )[0]
    if event_count == 0:
        failures.append(f"fact_log_events has 0 rows for date_key={date_key}")

    null_value_count = hook.get_first(
        """
        SELECT count(*) FROM mart.fact_sensor_readings
        WHERE date_key = %(dk)s AND (value IS NULL OR device_key IS NULL OR metric_type IS NULL)
        """,
        parameters={"dk": date_key},
    )[0]
    if null_value_count > 0:
        failures.append(f"{null_value_count} fact_sensor_readings rows have null critical columns")

    dup_readings = hook.get_first(
        """
        SELECT count(*) FROM (
            SELECT reading_id FROM mart.fact_sensor_readings
            WHERE date_key = %(dk)s
            GROUP BY reading_id HAVING count(*) > 1
        ) d
        """,
        parameters={"dk": date_key},
    )[0]
    if dup_readings > 0:
        failures.append(f"{dup_readings} duplicate reading_id values in fact_sensor_readings")

    orphan_devices = hook.get_first(
        """
        SELECT count(*) FROM mart.fact_sensor_readings f
        LEFT JOIN mart.dim_device d ON f.device_key = d.device_key
        WHERE f.date_key = %(dk)s AND d.device_key IS NULL
        """,
        parameters={"dk": date_key},
    )[0]
    if orphan_devices > 0:
        failures.append(f"{orphan_devices} fact_sensor_readings rows have no matching dim_device row")

    logger.info(
        "data_quality_checks ds=%s reading_count=%d event_count=%d null_critical=%d dup_readings=%d orphans=%d",
        ds, reading_count, event_count, null_value_count, dup_readings, orphan_devices,
    )

    if failures:
        raise AirflowException(f"Data quality checks failed for ds={ds}: " + "; ".join(failures))
