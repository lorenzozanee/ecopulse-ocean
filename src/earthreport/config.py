"""Immutable configuration and data models for the earth report system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple


@dataclass(frozen=True)
class RegionConfig:
    name: str
    name_cn: str
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float


@dataclass(frozen=True)
class SimConfig:
    seed: int = 42
    hours: int = 24
    interval_minutes: int = 60
    noise_amplitude: float = 1.0


@dataclass(frozen=True)
class LLMConfig:
    provider: str = "claude"
    model: str = ""
    temperature: float = 0.3
    max_tokens: int = 800

    def __post_init__(self) -> None:
        if not self.model:
            object.__setattr__(
                self, "model",
                "claude-sonnet-4-6" if self.provider == "claude" else "gpt-4o"
            )


@dataclass(frozen=True)
class ReportConfig:
    output_dir: str = "reports"
    format: str = "html"


class Stats1D(NamedTuple):
    mean: float
    std: float
    min_val: float
    max_val: float


class OceanMetrics(NamedTuple):
    timestamp: str
    sst: float
    chl: float
    poc_flux: float
    mld: float
    salinity: float
    current_u: float
    current_v: float


class DenoisedSignal(NamedTuple):
    raw: list[float]
    filtered: list[float]
    snr_before: float
    snr_after: float
    gain_db: float


REGIONS: dict[str, RegionConfig] = {
    "scs": RegionConfig("scs", "南海", 5.0, 22.0, 110.0, 120.0),
    "na":  RegionConfig("na",  "北大西洋", 35.0, 60.0, -60.0, -10.0),
    "so":  RegionConfig("so",  "南大洋", -70.0, -45.0, -180.0, 180.0),
    "ep":  RegionConfig("ep",  "东太平洋", -10.0, 10.0, -120.0, -80.0),
    "io":  RegionConfig("io",  "北印度洋", 0.0, 20.0, 60.0, 90.0),
}
