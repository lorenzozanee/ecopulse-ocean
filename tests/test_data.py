"""Tests for Module A: data simulator and denoiser."""

import numpy as np
import pytest

from earthreport.config import REGIONS, SimConfig
from earthreport.data.denoiser import denoise_pipeline, kalman_denoise, rlc_signal
from earthreport.data.simulator import compute_stats, generate_ocean_data


class TestSimulator:
    def test_deterministic_seed(self):
        a = generate_ocean_data(REGIONS["scs"], SimConfig(seed=42))
        b = generate_ocean_data(REGIONS["scs"], SimConfig(seed=42))
        for i in range(len(a)):
            assert a[i].sst == b[i].sst
            assert a[i].chl == b[i].chl

    def test_different_seed_produces_variation(self):
        a = generate_ocean_data(REGIONS["scs"], SimConfig(seed=1))
        b = generate_ocean_data(REGIONS["scs"], SimConfig(seed=2))
        diffs = sum(abs(a[i].sst - b[i].sst) for i in range(len(a)))
        assert diffs > 0.01

    def test_output_length(self):
        metrics = generate_ocean_data(REGIONS["na"], SimConfig(hours=24, interval_minutes=60))
        assert len(metrics) == 24

    def test_metrics_in_physical_range(self):
        metrics = generate_ocean_data(REGIONS["scs"])
        for m in metrics:
            assert 10 < m.sst < 40, f"SST {m.sst} out of range"
            assert 0.01 < m.chl < 10, f"Chl {m.chl} out of range"
            assert 0.01 < m.poc_flux < 20, f"POC flux {m.poc_flux} out of range"
            assert 1 < m.mld < 200, f"MLD {m.mld} out of range"

    def test_all_regions(self):
        for key in REGIONS:
            metrics = generate_ocean_data(REGIONS[key])
            assert len(metrics) > 0

    def test_compute_stats(self):
        metrics = generate_ocean_data(REGIONS["ep"], SimConfig(seed=42))
        stats = compute_stats(metrics)
        assert "sst_mean" in stats
        assert "chl_std" in stats
        assert stats["sst_min"] <= stats["sst_mean"] <= stats["sst_max"]


class TestDenoiser:
    def test_rlc_signal_length(self):
        sig = rlc_signal(hours=1, sample_rate_hz=1.0)
        assert len(sig) == 3600

    def test_kalman_reduces_variance(self):
        sig = rlc_signal(hours=2, sample_rate_hz=0.1, noise_sigma=0.2)
        filtered = kalman_denoise(sig)
        assert np.var(filtered) < np.var(sig)

    def test_denoise_pipeline_gain_positive(self):
        sig = rlc_signal(hours=1, sample_rate_hz=0.1, noise_sigma=0.15)
        result = denoise_pipeline(sig)
        assert result.gain_db > 0, f"Expected positive gain, got {result.gain_db}dB"
        assert len(result.filtered) == len(sig)
