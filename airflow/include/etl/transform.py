"""Validation + cleaning of raw sensor/log partitions.

Reads the raw JSONL shards for a partition, applies data-quality fixes, and
writes a cleaned Parquet file to a local staging path. Only the staging file
path is passed between tasks (via XCom) — not the DataFrame itself — to keep
XCom payloads small.
"""
from __future__ import annotations

import logging

import pandas as pd

from generator.devices import METRIC_BOUNDS, METRIC_UNITS

logger = logging.getLogger(__name__)

STAGING_DIR = "/opt/airflow/data/staging"

METRIC_TYPE_TO_UNIT = {metric_type: unit for metric_type, unit in METRIC_UNITS.values()}

KNOWN_LOG_LEVELS = {"INFO", "WARNING", "ERROR", "CRITICAL"}


def _read_jsonl(files: list[str]) -> pd.DataFrame:
    frames = [pd.read_json(f, lines=True) for f in files]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def clean_sensor_readings(files: list[str], ds: str) -> str:
    """Clean a day's sensor readings and write the result to a staging Parquet file.

    Returns the staging file path.
    """
    df = _read_jsonl(files)
    raw_count = len(df)

    out_path = f"{STAGING_DIR}/sensors/dt={ds}/cleaned.parquet"
    _ensure_parent(out_path)

    if df.empty:
        pd.DataFrame(
            columns=["reading_id", "device_id", "metric_type", "value", "unit", "reading_ts", "is_anomaly", "dt"]
        ).to_parquet(out_path)
        return out_path

    df["reading_ts"] = pd.to_datetime(df["reading_ts"], errors="coerce", utc=True)
    bad_ts = df["reading_ts"].isna().sum()
    df = df.dropna(subset=["reading_ts"])

    null_value = df["value"].isna().sum()
    df = df.dropna(subset=["value"])

    df["unit"] = df.apply(
        lambda row: row["unit"] if pd.notna(row["unit"]) else METRIC_TYPE_TO_UNIT.get(row["metric_type"]),
        axis=1,
    )

    before_dedup = len(df)
    df = df.drop_duplicates(subset=["reading_id"], keep="first")
    duplicates_dropped = before_dedup - len(df)

    df["value"] = df["value"].astype(float)

    def _is_anomaly(row) -> bool:
        bounds = METRIC_BOUNDS.get(row["metric_type"])
        if bounds is None:
            return False
        lo, hi = bounds
        return not (lo <= row["value"] <= hi)

    df["is_anomaly"] = df.apply(_is_anomaly, axis=1)
    df["dt"] = ds

    logger.info(
        "clean_sensor_readings ds=%s raw=%d bad_timestamp=%d null_value=%d duplicates=%d cleaned=%d anomalies=%d",
        ds, raw_count, bad_ts, null_value, duplicates_dropped, len(df), int(df["is_anomaly"].sum()),
    )

    df.to_parquet(out_path)
    return out_path


def clean_log_events(files: list[str], ds: str) -> str:
    """Clean a day's log events and write the result to a staging Parquet file.

    Returns the staging file path.
    """
    df = _read_jsonl(files)
    raw_count = len(df)

    out_path = f"{STAGING_DIR}/logs/dt={ds}/cleaned.parquet"
    _ensure_parent(out_path)

    if df.empty:
        pd.DataFrame(columns=["log_id", "service", "level", "message", "event_ts", "dt"]).to_parquet(out_path)
        return out_path

    df["event_ts"] = pd.to_datetime(df["event_ts"], errors="coerce", utc=True)
    bad_ts = df["event_ts"].isna().sum()
    df = df.dropna(subset=["event_ts"])

    df.loc[~df["level"].isin(KNOWN_LOG_LEVELS), "level"] = "UNKNOWN"

    before_dedup = len(df)
    df = df.drop_duplicates(subset=["log_id"], keep="first")
    duplicates_dropped = before_dedup - len(df)

    df["dt"] = ds

    logger.info(
        "clean_log_events ds=%s raw=%d bad_timestamp=%d duplicates=%d cleaned=%d",
        ds, raw_count, bad_ts, duplicates_dropped, len(df),
    )

    df.to_parquet(out_path)
    return out_path


def _ensure_parent(path: str) -> None:
    from pathlib import Path

    Path(path).parent.mkdir(parents=True, exist_ok=True)
