import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator.devices import DEVICE_IDS, DEVICES
from generator.logs import generate_log_partition
from generator.sensors import generate_sensor_partition


def _read_jsonl(paths):
    rows = []
    for p in paths:
        with open(p) as f:
            for line in f:
                rows.append(json.loads(line))
    return rows


def test_device_registry_is_nonempty_and_unique():
    assert len(DEVICES) > 0
    assert len(DEVICE_IDS) == len(set(DEVICE_IDS))


def test_generate_sensor_partition(tmp_path):
    files = generate_sensor_partition("2026-08-19", str(tmp_path))
    assert len(files) == 3
    for f in files:
        assert Path(f).exists()

    rows = _read_jsonl(files)
    assert len(rows) > 0
    assert any(r["value"] is None for r in rows), "expected some null values to be injected"
    assert any(r["device_id"] not in DEVICE_IDS for r in rows), "expected some unknown device_ids"

    reading_ids = [r["reading_id"] for r in rows]
    assert len(reading_ids) != len(set(reading_ids)), "expected some duplicate reading_ids"


def test_generate_sensor_partition_is_deterministic(tmp_path):
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    files1 = generate_sensor_partition("2026-08-19", str(out1))
    files2 = generate_sensor_partition("2026-08-19", str(out2))
    assert _read_jsonl(files1) == _read_jsonl(files2)


def test_generate_log_partition(tmp_path):
    files = generate_log_partition("2026-08-19", str(tmp_path))
    assert len(files) == 2
    rows = _read_jsonl(files)
    assert len(rows) > 0
    levels = {r["level"] for r in rows}
    assert levels <= {"INFO", "WARNING", "ERROR", "CRITICAL"}
    services = {r["service"] for r in rows}
    assert len(services) == 5
