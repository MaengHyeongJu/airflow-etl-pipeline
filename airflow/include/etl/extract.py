"""Discovery of landed raw files for a given partition.

Deliberately decoupled from the generation step: a real ingestion DAG
shouldn't assume it knows exactly how files arrived, only where to look.
"""
from __future__ import annotations

from pathlib import Path

RAW_DATA_DIR = "/opt/airflow/data/raw"


def discover_partition_files(source: str, ds: str, base_dir: str = RAW_DATA_DIR) -> list[str]:
    """Return sorted file paths for `<base_dir>/<source>/dt=<ds>/*.jsonl`."""
    partition_dir = Path(base_dir) / source / f"dt={ds}"
    if not partition_dir.exists():
        return []
    return sorted(str(p) for p in partition_dir.glob("*.jsonl"))
