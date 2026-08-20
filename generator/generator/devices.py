"""Static registry of virtual IoT devices used across all generated partitions.

Kept static (not randomized per run) so `dim_device` upserts are stable and
device history (install_date, location) is consistent across backfills.
"""
from __future__ import annotations

from dataclasses import dataclass

METRIC_UNITS = {
    "temperature": ("temperature_c", "C"),
    "humidity": ("humidity_pct", "%"),
    "pressure": ("pressure_hpa", "hPa"),
    "vibration": ("vibration_mm_s", "mm/s"),
    "power_meter": ("power_kw", "kW"),
}

# (mean, stddev) used to synthesize plausible readings per metric type
METRIC_DISTRIBUTIONS = {
    "temperature_c": (22.0, 3.0),
    "humidity_pct": (45.0, 8.0),
    "pressure_hpa": (1013.0, 6.0),
    "vibration_mm_s": (1.2, 0.5),
    "power_kw": (14.0, 4.0),
}

# Values outside these bounds are considered anomalous for their metric type
METRIC_BOUNDS = {
    "temperature_c": (-10.0, 60.0),
    "humidity_pct": (0.0, 100.0),
    "pressure_hpa": (950.0, 1080.0),
    "vibration_mm_s": (0.0, 10.0),
    "power_kw": (0.0, 50.0),
}

_LOCATIONS = [
    "Warehouse A - Line 1",
    "Warehouse A - Line 2",
    "Warehouse B - Line 1",
    "Warehouse B - Line 2",
    "Plant 1 - Assembly",
    "Plant 1 - Packaging",
    "Plant 2 - Assembly",
    "Cold Storage - Bay 1",
    "Cold Storage - Bay 2",
    "Loading Dock",
]

_DEVICE_TYPES = ["temperature", "humidity", "pressure", "vibration", "power_meter"]


@dataclass(frozen=True)
class Device:
    device_id: str
    device_type: str
    location: str
    install_date: str  # ISO date string

    @property
    def metric_type(self) -> str:
        return METRIC_UNITS[self.device_type][0]

    @property
    def unit(self) -> str:
        return METRIC_UNITS[self.device_type][1]


def _build_registry(count: int = 26) -> list[Device]:
    devices = []
    for i in range(1, count + 1):
        device_type = _DEVICE_TYPES[(i - 1) % len(_DEVICE_TYPES)]
        location = _LOCATIONS[(i - 1) % len(_LOCATIONS)]
        # Spread install dates across the last ~2 years, deterministically
        year = 2024 + ((i - 1) // 12)
        month = ((i - 1) % 12) + 1
        install_date = f"{year:04d}-{month:02d}-01"
        devices.append(
            Device(
                device_id=f"sensor-{i:03d}",
                device_type=device_type,
                location=location,
                install_date=install_date,
            )
        )
    return devices


DEVICES: list[Device] = _build_registry()
DEVICE_IDS: list[str] = [d.device_id for d in DEVICES]
