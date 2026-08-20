"""Standalone CLI for the generator package, independent of Airflow.

    python -m generator.cli --ds 2026-08-19 --out data/raw
"""
from __future__ import annotations

import argparse

from .logs import generate_log_partition
from .sensors import generate_sensor_partition


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ds", required=True, help="Execution date, YYYY-MM-DD")
    parser.add_argument("--out", required=True, help="Base output directory (e.g. data/raw)")
    args = parser.parse_args()

    sensor_files = generate_sensor_partition(args.ds, args.out)
    log_files = generate_log_partition(args.ds, args.out)

    print(f"Wrote {len(sensor_files)} sensor shard(s):")
    for f in sensor_files:
        print(f"  {f}")
    print(f"Wrote {len(log_files)} log shard(s):")
    for f in log_files:
        print(f"  {f}")


if __name__ == "__main__":
    main()
