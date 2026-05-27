"""Carbon pump efficiency calculations — deterministic formulas.

LLM only does qualitative interpretation; all numbers are computed here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CarbonMetrics:
    export_ratio: float
    martin_b: float
    poc_at_100m: float
    carbon_pump_efficiency_percentile: float
    grade: str  # A, B, C, D


def compute_export_ratio(poc_surface: float, poc_at_depth: float, depth_m: float = 100.0) -> float:
    if poc_surface <= 0:
        return 0.0
    return poc_at_depth / poc_surface


def fit_martin_curve(poc_surface: float, poc_at_depth: float,
                     ref_depth: float = 10.0, target_depth: float = 100.0) -> float:
    if poc_surface <= 0 or poc_at_depth <= 0:
        return 0.86
    ratio = poc_at_depth / poc_surface
    b = -math.log(ratio) / math.log(target_depth / ref_depth)
    return round(max(0.3, min(1.5, b)), 2)


def compute_pump_efficiency_percentile(martin_b: float, poc_at_100m: float) -> float:
    flux_score = min(1.0, poc_at_100m / 8.0)
    b_score = min(1.0, 1.0 / max(0.3, martin_b))
    score = (flux_score + b_score) / 2
    return round(score * 100, 1)


def grade_efficiency(percentile: float) -> str:
    if percentile >= 75:
        return "A"
    elif percentile >= 50:
        return "B"
    elif percentile >= 25:
        return "C"
    return "D"


def analyze_carbon_pump(
    chl_surface: float,
    poc_surface: float,
    poc_at_100m: float,
) -> CarbonMetrics:
    export_ratio = compute_export_ratio(poc_surface, poc_at_100m)
    martin_b = fit_martin_curve(poc_surface, poc_at_100m)
    percentile = compute_pump_efficiency_percentile(martin_b, poc_at_100m)
    grade = grade_efficiency(percentile)
    return CarbonMetrics(
        export_ratio=round(export_ratio, 3),
        martin_b=martin_b,
        poc_at_100m=round(poc_at_100m, 2),
        carbon_pump_efficiency_percentile=percentile,
        grade=grade,
    )
