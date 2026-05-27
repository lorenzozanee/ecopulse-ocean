"""Tests for Module B: LLM analyst and carbon calculations."""

import pytest

from earthreport.analyst.carbon import (
    CarbonMetrics,
    analyze_carbon_pump,
    compute_export_ratio,
    fit_martin_curve,
    grade_efficiency,
)
from earthreport.analyst.llm import MockClient, get_llm
from earthreport.analyst.prompts import (
    biodiversity_prompt,
    carbon_efficiency_prompt,
    heatwave_risk_prompt,
    signal_interpret_prompt,
)
from earthreport.analyst.report import ReportGenerator


class TestCarbonCalculations:
    def test_export_ratio_basic(self):
        assert compute_export_ratio(5.0, 0.5) == 0.1

    def test_export_ratio_zero_surface(self):
        assert compute_export_ratio(0.0, 1.0) == 0.0

    def test_martin_b_typical(self):
        b = fit_martin_curve(5.0, 0.7)
        assert 0.3 < b < 1.5

    def test_martin_b_higher_flux_gives_lower_b(self):
        b1 = fit_martin_curve(5.0, 2.0)
        b2 = fit_martin_curve(5.0, 0.5)
        assert b1 < b2

    def test_grade_efficiency(self):
        assert grade_efficiency(80) == "A"
        assert grade_efficiency(60) == "B"
        assert grade_efficiency(40) == "C"
        assert grade_efficiency(10) == "D"

    def test_analyze_carbon_pump_returns_all_fields(self):
        result = analyze_carbon_pump(2.0, 5.0, 1.0)
        assert isinstance(result, CarbonMetrics)
        assert result.grade in ("A", "B", "C", "D")
        assert 0 < result.export_ratio <= 1.0
        assert 0.3 <= result.martin_b <= 1.5


class TestPrompts:
    def test_carbon_prompt_renders(self):
        carbon = CarbonMetrics(0.2, 0.86, 1.07, 62.5, "B")
        prompt = carbon_efficiency_prompt("南海", carbon, 28.4, 1.82)
        assert "南海" in prompt
        assert "62%" in prompt
        assert "B" in prompt

    def test_heatwave_prompt_renders(self):
        prompt = heatwave_risk_prompt("北大西洋", 29.0, 1.2, 27.8)
        assert "北大西洋" in prompt
        assert "1.2" in prompt

    def test_biodiversity_prompt_renders(self):
        prompt = biodiversity_prompt("南大洋", 1.5, 0.4)
        assert "南大洋" in prompt
        assert "1.5" in prompt

    def test_signal_interpret_prompt_renders(self):
        prompt = signal_interpret_prompt(8.0, 22.0, 14.0, "昼夜振荡")
        assert "22.0" in prompt
        assert "14.0" in prompt


class TestMockLLM:
    def test_mock_returns_nonempty(self):
        llm = MockClient()
        for prompt in [
            carbon_efficiency_prompt(
                "南海", CarbonMetrics(0.2, 0.86, 1.07, 62.5, "B"), 28.4, 1.82
            ),
            heatwave_risk_prompt("南海", 28.4, 0.9, 27.5),
            biodiversity_prompt("南海", 1.82, 0.31),
            signal_interpret_prompt(8.0, 22.0, 14.0, "昼夜振荡"),
        ]:
            text = llm.generate(prompt)
            assert len(text) > 20

    def test_get_llm_mock(self):
        llm = get_llm("mock")
        assert isinstance(llm, MockClient)

    def test_get_llm_invalid(self):
        with pytest.raises(ValueError):
            get_llm("nonexistent")


class TestReportGenerator:
    def test_generate_with_mock(self):
        llm = MockClient()
        gen = ReportGenerator(llm)
        report = gen.generate("南海", 28.4, 1.82, 0.31, 5.0, 1.07, 8.0, 22.0, 14.0)
        assert report.region_name == "南海"
        assert report.carbon.grade in ("A", "B", "C", "D")
        assert len(report.carbon.narrative) > 20
        assert report.heatwave.grade in ("A", "B", "C", "D")

    def test_to_dict(self):
        llm = MockClient()
        gen = ReportGenerator(llm)
        report = gen.generate("南海", 28.4, 1.82, 0.31, 5.0, 1.07, 8.0, 22.0, 14.0)
        d = report.to_dict()
        assert d["region"] == "南海"
        assert len(d["sections"]) == 4
        assert all("narrative" in s for s in d["sections"])
