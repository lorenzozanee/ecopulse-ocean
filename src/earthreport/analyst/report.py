"""Health report aggregator — combines deterministic metrics with LLM narrative."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from earthreport.analyst.carbon import analyze_carbon_pump
from earthreport.analyst.prompts import (
    biodiversity_prompt,
    carbon_efficiency_prompt,
    heatwave_risk_prompt,
    signal_interpret_prompt,
)

if TYPE_CHECKING:
    from earthreport.analyst.llm import LLMClient


@dataclass(frozen=True)
class ReportSection:
    title: str
    grade: str
    narrative: str


@dataclass(frozen=True)
class HealthReport:
    region_name: str
    carbon: ReportSection
    heatwave: ReportSection
    biodiversity: ReportSection
    rlc_signal: ReportSection

    def to_dict(self) -> dict:
        return {
            "region": self.region_name,
            "sections": [
                {"title": self.carbon.title, "grade": self.carbon.grade,
                 "narrative": self.carbon.narrative},
                {"title": self.heatwave.title, "grade": self.heatwave.grade,
                 "narrative": self.heatwave.narrative},
                {"title": self.biodiversity.title, "grade": self.biodiversity.grade,
                 "narrative": self.biodiversity.narrative},
                {"title": self.rlc_signal.title, "grade": self.rlc_signal.grade,
                 "narrative": self.rlc_signal.narrative},
            ],
        }


class ReportGenerator:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    def generate(
        self,
        region_cn: str,
        sst_mean: float,
        chl_mean: float,
        chl_std: float,
        poc_surface: float,
        poc_at_100m: float,
        snr_before: float,
        snr_after: float,
        gain_db: float,
    ) -> HealthReport:
        carbon = analyze_carbon_pump(chl_mean, poc_surface, poc_at_100m)
        sst_anomaly = max(0, sst_mean - 27.5)
        climatology = sst_mean - sst_anomaly

        carbon_text = self._llm.generate(
            carbon_efficiency_prompt(region_cn, carbon, sst_mean, chl_mean)
        )
        heatwave_text = self._llm.generate(
            heatwave_risk_prompt(region_cn, sst_mean, sst_anomaly, climatology)
        )
        biodiversity_text = self._llm.generate(
            biodiversity_prompt(region_cn, chl_mean, chl_std)
        )
        signal_pattern = "昼夜振荡 + 半日潮周期"
        rlc_text = self._llm.generate(
            signal_interpret_prompt(snr_before, snr_after, gain_db, signal_pattern)
        )

        return HealthReport(
            region_name=region_cn,
            carbon=ReportSection("碳汇效率", carbon.grade, carbon_text.strip()),
            heatwave=ReportSection("海洋热浪风险", self._heatwave_grade(sst_anomaly),
                                   heatwave_text.strip()),
            biodiversity=ReportSection("生物多样性代理",
                                       self._biodiversity_grade(chl_std, chl_mean),
                                       biodiversity_text.strip()),
            rlc_signal=ReportSection("RLC传感器信号", "",
                                     rlc_text.strip()),
        )

    @staticmethod
    def _heatwave_grade(anomaly: float) -> str:
        if anomaly >= 1.5:
            return "D"
        elif anomaly >= 1.0:
            return "C"
        elif anomaly >= 0.5:
            return "B"
        return "A"

    @staticmethod
    def _biodiversity_grade(chl_std: float, chl_mean: float) -> str:
        cv = chl_std / max(chl_mean, 0.01)
        if cv >= 0.6:
            return "C"
        elif cv >= 0.35:
            return "B"
        return "A"
