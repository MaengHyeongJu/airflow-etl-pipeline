"""Daily ETL: virtual sensor/log data -> collect -> clean -> load -> data mart.

    [generate_sensors, generate_logs] >> discover_files
      >> [clean_sensors, clean_logs]
      >> [load_staging_sensors, load_staging_logs]
      >> upsert_dim_device >> upsert_dim_date
      >> [merge_fact_sensor_readings, merge_fact_log_events]
      >> build_daily_aggregates
      >> data_quality_checks

Uses insert-overwrite-by-partition throughout (delete rows for `ds`, then
insert), so every task is safe to rerun and `airflow dags backfill` works
correctly.
"""
from __future__ import annotations

import sys
from datetime import datetime

from airflow.exceptions import AirflowSkipException
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.sdk import dag, task

sys.path.insert(0, "/opt/airflow/include")

from etl.extract import discover_partition_files  # noqa: E402
from etl.load import (  # noqa: E402
    load_staging_log_events,
    load_staging_sensor_readings,
    upsert_dim_device,
)
from etl.quality_checks import run_data_quality_checks  # noqa: E402
from etl.transform import clean_log_events, clean_sensor_readings  # noqa: E402
from generator.logs import generate_log_partition  # noqa: E402
from generator.sensors import generate_sensor_partition  # noqa: E402

RAW_DATA_DIR = "/opt/airflow/data/raw"
DATAMART_CONN_ID = "datamart_postgres"


@dag(
    dag_id="etl_pipeline",
    description="Virtual sensor/log ingestion -> clean -> load -> Postgres data mart",
    schedule="@daily",
    start_date=datetime(2026, 8, 1),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 1},
    template_searchpath=["/opt/airflow/include/sql"],
    tags=["etl", "portfolio"],
)
def etl_pipeline():
    @task
    def generate_sensor_data(ds: str) -> None:
        generate_sensor_partition(ds, RAW_DATA_DIR)

    @task
    def generate_log_data(ds: str) -> None:
        generate_log_partition(ds, RAW_DATA_DIR)

    @task
    def discover_files(source: str, ds: str) -> list[str]:
        files = discover_partition_files(source, ds, RAW_DATA_DIR)
        if not files:
            raise AirflowSkipException(f"No files found for source={source} dt={ds}")
        return files

    @task
    def clean_sensors(files: list[str], ds: str) -> str:
        return clean_sensor_readings(files, ds)

    @task
    def clean_logs(files: list[str], ds: str) -> str:
        return clean_log_events(files, ds)

    @task
    def load_sensors(staging_path: str, ds: str) -> int:
        return load_staging_sensor_readings(staging_path, ds)

    @task
    def load_logs(staging_path: str, ds: str) -> int:
        return load_staging_log_events(staging_path, ds)

    @task
    def upsert_devices(sensors_loaded: int, logs_loaded: int) -> int:
        return upsert_dim_device()

    @task
    def data_quality_checks(ds: str) -> None:
        run_data_quality_checks(ds)

    gen_sensors = generate_sensor_data(ds="{{ ds }}")
    gen_logs = generate_log_data(ds="{{ ds }}")

    sensor_files = discover_files.override(task_id="discover_sensor_files")(
        source="sensors", ds="{{ ds }}"
    )
    log_files = discover_files.override(task_id="discover_log_files")(
        source="logs", ds="{{ ds }}"
    )
    gen_sensors >> sensor_files
    gen_logs >> log_files

    cleaned_sensors = clean_sensors(sensor_files, ds="{{ ds }}")
    cleaned_logs = clean_logs(log_files, ds="{{ ds }}")

    loaded_sensors = load_sensors(cleaned_sensors, ds="{{ ds }}")
    loaded_logs = load_logs(cleaned_logs, ds="{{ ds }}")

    devices = upsert_devices(loaded_sensors, loaded_logs)

    dim_date = SQLExecuteQueryOperator(
        task_id="upsert_dim_date",
        conn_id=DATAMART_CONN_ID,
        sql="upsert_dim_date.sql",
    )
    devices >> dim_date

    merge_sensor_readings = SQLExecuteQueryOperator(
        task_id="merge_fact_sensor_readings",
        conn_id=DATAMART_CONN_ID,
        sql="merge_fact_sensor_readings.sql",
        split_statements=True,
    )
    merge_log_events = SQLExecuteQueryOperator(
        task_id="merge_fact_log_events",
        conn_id=DATAMART_CONN_ID,
        sql="merge_fact_log_events.sql",
        split_statements=True,
    )
    dim_date >> [merge_sensor_readings, merge_log_events]

    aggregates = SQLExecuteQueryOperator(
        task_id="build_daily_aggregates",
        conn_id=DATAMART_CONN_ID,
        sql="build_daily_aggregates.sql",
        split_statements=True,
    )
    [merge_sensor_readings, merge_log_events] >> aggregates

    dq_checks = data_quality_checks(ds="{{ ds }}")
    aggregates >> dq_checks


etl_pipeline()
