"""Synthetic sensor reading generation.

Writes one day's worth of IoT sensor readings for every device in the
registry into a `dt=<ds>` partitioned landing directory, as JSON Lines split
across a few shard files (simulating several upstream feeds landing in the
same partition).

Data is intentionally messy — a real ingestion source doesn't send perfectly
clean data, and the Airflow DAG's "clean" step needs real work to do:
  - ~2% of readings have a null `value`
  - ~1% are exact duplicates (same reading_id) of another row in the partition
  - ~1% are out-of-range spikes for their metric type
  - a handful have an unparsable `reading_ts`
  - ~1% reference a `device_id` that isn't in the device registry
    (simulates a misconfigured / late-registered sensor)
"""
from __future__ import annotations

import json
import random
import uuid
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from .devices import DEVICES, METRIC_BOUNDS, METRIC_DISTRIBUTIONS

READINGS_PER_DEVICE_RANGE = (80, 150)
NUM_SHARDS = 3

NULL_VALUE_RATE = 0.02
DUPLICATE_RATE = 0.01
SPIKE_RATE = 0.01
BAD_TIMESTAMP_RATE = 0.005
UNKNOWN_DEVICE_RATE = 0.01


def _random_ts_within_day(ds: date, rng: random.Random) -> datetime:
    day_start = datetime.combine(ds, time.min, tzinfo=timezone.utc)
    seconds_offset = rng.randint(0, 24 * 60 * 60 - 1)
    return day_start + timedelta(seconds=seconds_offset)


def _make_reading(device, ts: datetime, rng: random.Random) -> dict:
    mean, stddev = METRIC_DISTRIBUTIONS[device.metric_type]
    value = round(rng.gauss(mean, stddev), 2)
    return {
        "reading_id": str(uuid.UUID(int=rng.getrandbits(128))),
        "device_id": device.device_id,
        "metric_type": device.metric_type,
        "value": value,
        "unit": device.unit,
        "reading_ts": ts.isoformat(),
    }


def _inject_spike(reading: dict, rng: random.Random) -> None:
    lo, hi = METRIC_BOUNDS[reading["metric_type"]]
    span = hi - lo
    reading["value"] = round(hi + span * rng.uniform(0.5, 2.0), 2)


def generate_sensor_partition(ds: str, out_dir: str, seed: int | None = None) -> list[str]:
    """Generate one day's sensor readings for all devices.

    Args:
        ds: execution date as 'YYYY-MM-DD'.
        out_dir: base output directory; files are written under
            `<out_dir>/sensors/dt=<ds>/`.
        seed: optional RNG seed for reproducibility (defaults to a seed
            derived from `ds` so re-running the same partition is stable).

    Returns:
        List of written file paths (as strings).
    """
    ds_date = date.fromisoformat(ds)
    rng = random.Random(seed if seed is not None else f"sensors-{ds}")

    partition_dir = Path(out_dir) / "sensors" / f"dt={ds}"
    partition_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for device in DEVICES:
        n = rng.randint(*READINGS_PER_DEVICE_RANGE)
        for _ in range(n):
            ts = _random_ts_within_day(ds_date, rng)
            rows.append(_make_reading(device, ts, rng))

    # Inject messiness
    for row in rows:
        if rng.random() < NULL_VALUE_RATE:
            row["value"] = None
        elif rng.random() < SPIKE_RATE:
            _inject_spike(row, rng)
        if rng.random() < BAD_TIMESTAMP_RATE:
            row["reading_ts"] = "not-a-timestamp"
        if rng.random() < UNKNOWN_DEVICE_RATE:
            row["device_id"] = f"unregistered-{rng.randint(900, 999)}"

    duplicate_count = max(1, int(len(rows) * DUPLICATE_RATE))
    rows.extend(dict(row) for row in rng.sample(rows, duplicate_count))

    rng.shuffle(rows)

    shard_files = [partition_dir / f"sensors_{ds}_{i}.jsonl" for i in range(NUM_SHARDS)]
    handles = [f.open("w") for f in shard_files]
    try:
        for i, row in enumerate(rows):
            handle = handles[i % NUM_SHARDS]
            handle.write(json.dumps(row) + "\n")
    finally:
        for h in handles:
            h.close()

    return [str(f) for f in shard_files]
