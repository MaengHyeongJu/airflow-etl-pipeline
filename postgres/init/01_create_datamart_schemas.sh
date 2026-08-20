#!/usr/bin/env bash
# Creates the staging + mart schemas/tables inside the data mart DB and grants
# read-only SELECT on the mart schema to the dashboard reader role.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATAMART_DB_NAME" <<-EOSQL
    CREATE SCHEMA IF NOT EXISTS staging AUTHORIZATION "${DATAMART_ETL_USER}";
    CREATE SCHEMA IF NOT EXISTS mart AUTHORIZATION "${DATAMART_ETL_USER}";

    GRANT USAGE ON SCHEMA staging, mart TO "${DATAMART_ETL_USER}";
    GRANT USAGE ON SCHEMA mart TO "${DATAMART_READER_USER}";
    ALTER DEFAULT PRIVILEGES FOR ROLE "${DATAMART_ETL_USER}" IN SCHEMA mart
        GRANT SELECT ON TABLES TO "${DATAMART_READER_USER}";

    SET ROLE "${DATAMART_ETL_USER}";

    -- ============ staging: raw, partition-overwrite landing tables ============
    CREATE TABLE IF NOT EXISTS staging.sensor_readings_raw (
        reading_id   UUID NOT NULL,
        device_id    TEXT,
        metric_type  TEXT,
        value        DOUBLE PRECISION,
        unit         TEXT,
        reading_ts   TIMESTAMPTZ,
        is_anomaly   BOOLEAN NOT NULL DEFAULT FALSE,
        dt           DATE NOT NULL,
        loaded_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS ix_sensor_readings_raw_dt ON staging.sensor_readings_raw (dt);

    CREATE TABLE IF NOT EXISTS staging.log_events_raw (
        log_id     UUID NOT NULL,
        service    TEXT,
        level      TEXT,
        message    TEXT,
        event_ts   TIMESTAMPTZ,
        dt         DATE NOT NULL,
        loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS ix_log_events_raw_dt ON staging.log_events_raw (dt);

    -- ============ mart: dimensional model ============
    CREATE TABLE IF NOT EXISTS mart.dim_device (
        device_key    SERIAL PRIMARY KEY,
        device_id     TEXT NOT NULL UNIQUE,
        device_type   TEXT NOT NULL,
        location      TEXT,
        install_date  DATE,
        is_active     BOOLEAN NOT NULL DEFAULT TRUE,
        updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS mart.dim_date (
        date_key      INT PRIMARY KEY,
        full_date     DATE NOT NULL UNIQUE,
        year          INT NOT NULL,
        month         INT NOT NULL,
        day           INT NOT NULL,
        day_of_week   INT NOT NULL,
        day_name      TEXT NOT NULL,
        week_of_year  INT NOT NULL,
        is_weekend    BOOLEAN NOT NULL
    );

    CREATE TABLE IF NOT EXISTS mart.fact_sensor_readings (
        reading_key  BIGSERIAL PRIMARY KEY,
        reading_id   UUID NOT NULL UNIQUE,
        device_key   INT NOT NULL REFERENCES mart.dim_device (device_key),
        date_key     INT NOT NULL REFERENCES mart.dim_date (date_key),
        metric_type  TEXT NOT NULL,
        value        DOUBLE PRECISION NOT NULL,
        unit         TEXT,
        reading_ts   TIMESTAMPTZ NOT NULL,
        is_anomaly   BOOLEAN NOT NULL DEFAULT FALSE
    );
    CREATE INDEX IF NOT EXISTS ix_fact_sensor_readings_date ON mart.fact_sensor_readings (date_key);
    CREATE INDEX IF NOT EXISTS ix_fact_sensor_readings_device_metric_date
        ON mart.fact_sensor_readings (device_key, metric_type, date_key);

    CREATE TABLE IF NOT EXISTS mart.fact_log_events (
        event_key  BIGSERIAL PRIMARY KEY,
        log_id     UUID NOT NULL UNIQUE,
        date_key   INT NOT NULL REFERENCES mart.dim_date (date_key),
        service    TEXT NOT NULL,
        level      TEXT NOT NULL,
        message    TEXT,
        event_ts   TIMESTAMPTZ NOT NULL
    );
    CREATE INDEX IF NOT EXISTS ix_fact_log_events_date ON mart.fact_log_events (date_key);
    CREATE INDEX IF NOT EXISTS ix_fact_log_events_service_level_date
        ON mart.fact_log_events (service, level, date_key);

    CREATE TABLE IF NOT EXISTS mart.agg_daily_device_metrics (
        date_key        INT NOT NULL REFERENCES mart.dim_date (date_key),
        device_key      INT NOT NULL REFERENCES mart.dim_device (device_key),
        metric_type     TEXT NOT NULL,
        reading_count   INT NOT NULL,
        avg_value       DOUBLE PRECISION,
        min_value       DOUBLE PRECISION,
        max_value       DOUBLE PRECISION,
        anomaly_count   INT NOT NULL DEFAULT 0,
        PRIMARY KEY (date_key, device_key, metric_type)
    );

    CREATE TABLE IF NOT EXISTS mart.agg_daily_log_summary (
        date_key      INT NOT NULL REFERENCES mart.dim_date (date_key),
        service       TEXT NOT NULL,
        level         TEXT NOT NULL,
        event_count   INT NOT NULL,
        PRIMARY KEY (date_key, service, level)
    );

    RESET ROLE;
EOSQL
