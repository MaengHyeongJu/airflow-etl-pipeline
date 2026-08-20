#!/usr/bin/env bash
# Runs once, on first container start, as the Postgres superuser ($POSTGRES_USER).
# Creates the Airflow metadata DB + the data mart DB, plus least-privilege roles
# for the ETL writer (Airflow) and the read-only dashboard API.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Airflow metadata DB + owner role
    CREATE ROLE "${AIRFLOW_DB_USER}" WITH LOGIN PASSWORD '${AIRFLOW_DB_PASSWORD}';
    CREATE DATABASE "${AIRFLOW_DB_NAME}" OWNER "${AIRFLOW_DB_USER}";

    -- Data mart DB
    CREATE DATABASE "${DATAMART_DB_NAME}";

    -- ETL writer role: used by Airflow to load staging tables and build the mart
    CREATE ROLE "${DATAMART_ETL_USER}" WITH LOGIN PASSWORD '${DATAMART_ETL_PASSWORD}';
    GRANT ALL PRIVILEGES ON DATABASE "${DATAMART_DB_NAME}" TO "${DATAMART_ETL_USER}";

    -- Dashboard reader role: used by the FastAPI backend, read-only
    CREATE ROLE "${DATAMART_READER_USER}" WITH LOGIN PASSWORD '${DATAMART_READER_PASSWORD}';
EOSQL
