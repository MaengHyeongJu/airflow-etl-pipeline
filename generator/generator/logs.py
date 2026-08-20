"""Synthetic application/service log generation.

Writes one day's worth of log events for a fixed set of services into a
`dt=<ds>` partitioned landing directory, as JSON Lines split across a few
shard files.
"""
from __future__ import annotations

import json
import random
import uuid
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

SERVICES = ["ingest-api", "auth-service", "worker-etl", "payment-gateway", "notification-svc"]

# Weighted so INFO dominates, like a real service under normal load
LEVEL_WEIGHTS = {
    "INFO": 0.78,
    "WARNING": 0.14,
    "ERROR": 0.07,
    "CRITICAL": 0.01,
}

_MESSAGE_TEMPLATES = {
    "INFO": [
        "request completed status=200 path={path} duration_ms={dur}",
        "health check ok",
        "cache hit key={key}",
        "job {job} finished successfully in {dur}ms",
        "connection pool size={n} active={active}",
    ],
    "WARNING": [
        "request slow status=200 path={path} duration_ms={dur}",
        "retrying downstream call attempt={n}",
        "cache miss key={key}, falling back to source",
        "connection pool near capacity active={active}/{n}",
        "deprecated endpoint {path} called",
    ],
    "ERROR": [
        "request failed status=500 path={path} duration_ms={dur}",
        "downstream timeout calling {job} after {dur}ms",
        "failed to acquire db connection pool_size={n}",
        "unhandled exception in {job}: NullPointerException",
    ],
    "CRITICAL": [
        "service {job} crashed, restarting",
        "database connection pool exhausted, rejecting requests",
        "out of memory in {job}",
    ],
}

_PATHS = ["/api/orders", "/api/users", "/api/payments", "/api/devices", "/api/health"]
_JOBS = ["etl-load", "reconcile-payments", "sync-devices", "cleanup-sessions"]

EVENTS_PER_SERVICE_RANGE = (150, 400)
NUM_SHARDS = 2


def _random_ts_within_day(ds: date, rng: random.Random) -> datetime:
    day_start = datetime.combine(ds, time.min, tzinfo=timezone.utc)
    seconds_offset = rng.randint(0, 24 * 60 * 60 - 1)
    return day_start + timedelta(seconds=seconds_offset)


def _pick_level(rng: random.Random) -> str:
    levels, weights = zip(*LEVEL_WEIGHTS.items())
    return rng.choices(levels, weights=weights, k=1)[0]


def _make_message(level: str, rng: random.Random) -> str:
    template = rng.choice(_MESSAGE_TEMPLATES[level])
    return template.format(
        path=rng.choice(_PATHS),
        dur=rng.randint(5, 4000),
        key=f"k-{rng.randint(1000, 9999)}",
        job=rng.choice(_JOBS),
        n=rng.randint(5, 50),
        active=rng.randint(1, 50),
    )


def generate_log_partition(ds: str, out_dir: str, seed: int | None = None) -> list[str]:
    """Generate one day's log events for all services.

    Args:
        ds: execution date as 'YYYY-MM-DD'.
        out_dir: base output directory; files are written under
            `<out_dir>/logs/dt=<ds>/`.
        seed: optional RNG seed (defaults to a seed derived from `ds`).

    Returns:
        List of written file paths (as strings).
    """
    ds_date = date.fromisoformat(ds)
    rng = random.Random(seed if seed is not None else f"logs-{ds}")

    partition_dir = Path(out_dir) / "logs" / f"dt={ds}"
    partition_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for service in SERVICES:
        n = rng.randint(*EVENTS_PER_SERVICE_RANGE)
        for _ in range(n):
            level = _pick_level(rng)
            ts = _random_ts_within_day(ds_date, rng)
            rows.append(
                {
                    "log_id": str(uuid.UUID(int=rng.getrandbits(128))),
                    "service": service,
                    "level": level,
                    "message": _make_message(level, rng),
                    "event_ts": ts.isoformat(),
                }
            )

    rng.shuffle(rows)

    shard_files = [partition_dir / f"logs_{ds}_{i}.jsonl" for i in range(NUM_SHARDS)]
    handles = [f.open("w") for f in shard_files]
    try:
        for i, row in enumerate(rows):
            handle = handles[i % NUM_SHARDS]
            handle.write(json.dumps(row) + "\n")
    finally:
        for h in handles:
            h.close()

    return [str(f) for f in shard_files]
