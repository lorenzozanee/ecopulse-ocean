"""Procedural ocean data generator with physical models."""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import numpy as np

from earthreport.config import OceanMetrics, RegionConfig, SimConfig


def _seasonal_factor(timestamp: datetime, lat: float) -> float:
    doy = timestamp.timetuple().tm_yday
    phase = (doy / 365) * 2 * math.pi
    return math.sin(phase if lat >= 0 else phase + math.pi)


def _diurnal_factor(hour: float) -> float:
    return math.sin((hour - 6) / 24 * 2 * math.pi)


def _tidal_factor(hour: float) -> float:
    return math.sin(hour / 12.42 * 2 * math.pi)


def _multi_octave(x: float, y: float, t: float, octaves: int = 3) -> float:
    value = 0.0
    for i in range(octaves):
        freq = 2.0 ** i
        amp = 1.0 / freq
        value += amp * math.sin(x * freq + t * 0.3 * freq) * math.cos(y * freq - t * 0.25 * freq)
    return value / (2.0 - 1.0 / (2 ** (octaves - 1)))


def generate_ocean_data(
    region: RegionConfig,
    config: SimConfig | None = None,
) -> list[OceanMetrics]:
    cfg = config or SimConfig()
    rng = np.random.default_rng(cfg.seed)
    lat = (region.lat_min + region.lat_max) / 2

    start = datetime(2026, 5, 27, 0, 0, 0)
    n_steps = cfg.hours * 60 // cfg.interval_minutes
    results: list[OceanMetrics] = []

    for step in range(n_steps):
        ts = start + timedelta(minutes=step * cfg.interval_minutes)
        hour = ts.hour + ts.minute / 60

        season = _seasonal_factor(ts, lat)
        diurnal = _diurnal_factor(hour)
        tidal = _tidal_factor(hour)
        spatial = _multi_octave(lat / 90, region.lon_min / 180, step / n_steps)

        base_sst = 25 + 5 * (1 - abs(lat) / 60)
        sst = base_sst + 3 * season + 2 * diurnal + 1.5 * spatial * cfg.noise_amplitude
        sst += rng.normal(0, 0.3)

        chl = 0.8 + 2.2 * max(0, season + 0.3) + 0.5 * abs(tidal)
        chl += 0.4 * spatial * cfg.noise_amplitude
        chl += rng.normal(0, 0.1)
        chl = max(0.1, chl)

        poc_surface = chl * 2.5 + rng.normal(0, 0.3)
        poc_flux = poc_surface * (100 / 10) ** (-0.86)
        poc_flux = max(0.1, poc_flux)

        mld_base = 40 + 20 * (1 - abs(lat) / 60)
        mld = mld_base - 15 * diurnal + 10 * abs(tidal)
        mld += rng.normal(0, 3)
        mld = max(5, mld)

        salinity = 35.0 - 2.5 * abs(lat) / 60 + 0.5 * spatial
        salinity += rng.normal(0, 0.1)

        current_u = 0.3 * spatial + 0.2 * tidal + rng.normal(0, 0.05)
        current_v = 0.2 * season + 0.15 * tidal + rng.normal(0, 0.05)

        results.append(OceanMetrics(
            timestamp=ts.isoformat(),
            sst=round(sst, 2),
            chl=round(chl, 3),
            poc_flux=round(poc_flux, 2),
            mld=round(mld, 1),
            salinity=round(salinity, 3),
            current_u=round(current_u, 3),
            current_v=round(current_v, 3),
        ))

    return results


def compute_stats(metrics: list[OceanMetrics]) -> dict[str, float]:
    arr = np.array([(m.sst, m.chl, m.poc_flux, m.mld, m.salinity) for m in metrics])
    labels = ["sst", "chl", "poc_flux", "mld", "salinity"]
    stats: dict[str, float] = {}
    for i, label in enumerate(labels):
        col = arr[:, i]
        stats[f"{label}_mean"] = float(np.mean(col))
        stats[f"{label}_std"] = float(np.std(col))
        stats[f"{label}_min"] = float(np.min(col))
        stats[f"{label}_max"] = float(np.max(col))
    return stats
