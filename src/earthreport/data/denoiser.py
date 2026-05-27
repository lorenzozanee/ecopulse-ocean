"""Signal denoising for RLC sensor data — Kalman filter + SNR estimation."""

from __future__ import annotations

import math

import numpy as np

from earthreport.config import DenoisedSignal


def rlc_signal(
    hours: float = 24, sample_rate_hz: float = 1.0, noise_sigma: float = 0.15
) -> list[float]:
    rng = np.random.default_rng(42)
    n = int(hours * 3600 * sample_rate_hz)
    t = np.arange(n) / sample_rate_hz
    hour = t / 3600
    clean = (
        0.35 * np.sin(hour / 24 * 2 * math.pi + 1.2)
        + 0.12 * np.sin(hour / 12.42 * 2 * math.pi)
        + 0.05 * np.sin(hour / 6 * 2 * math.pi + 0.7)
        + 0.02 * hour / 24
    )
    noisy = clean + rng.normal(0, noise_sigma, n)
    return noisy.tolist()


def kalman_denoise(
    signal: list[float],
    process_var: float = 0.001,
    measurement_var: float = 0.02,
) -> list[float]:
    n = len(signal)
    filtered = [0.0] * n
    x_est = signal[0]
    p_est = 1.0

    for k in range(n):
        x_pred = x_est
        p_pred = p_est + process_var
        kg = p_pred / (p_pred + measurement_var)
        x_est = x_pred + kg * (signal[k] - x_pred)
        p_est = (1 - kg) * p_pred
        filtered[k] = x_est

    return filtered


def compute_snr(signal: list[float], reference: list[float]) -> float:
    s = np.array(signal)
    ref = np.array(reference)
    noise = s - ref
    var_signal = float(np.var(ref))
    var_noise = float(np.var(noise))
    if var_noise < 1e-12:
        return float("inf")
    return float(10 * math.log10(var_signal / var_noise))


def denoise_pipeline(
    signal: list[float],
    process_var: float = 0.001,
    measurement_var: float = 0.02,
) -> DenoisedSignal:
    filtered = kalman_denoise(signal, process_var, measurement_var)
    sig_arr = np.array(signal)
    filt_arr = np.array(filtered)

    # Noise power before: estimated from high-frequency first-differences
    diffs = np.diff(sig_arr)
    noise_power_before = float(np.var(diffs) / 2)
    # Residual noise power after filtering
    noise_power_after = float(np.var(sig_arr - filt_arr))
    signal_power = float(np.var(filt_arr))

    eps = 1e-15
    snr_before = float(10 * math.log10(signal_power / (noise_power_before + eps)))
    snr_after_val = float(10 * math.log10(signal_power / (noise_power_after + eps)))
    gain_db = snr_after_val - snr_before

    return DenoisedSignal(
        raw=signal,
        filtered=filtered,
        snr_before=round(snr_before, 1),
        snr_after=round(snr_after_val, 1),
        gain_db=round(gain_db, 1),
    )
