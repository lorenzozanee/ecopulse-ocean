"""CLI entry point — argparse, mirrors oceanicdata-cli/main.py:54."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from earthreport import __version__
from earthreport.analyst.llm import get_llm
from earthreport.analyst.report import ReportGenerator
from earthreport.config import REGIONS, SimConfig
from earthreport.data.connectors import get_connector
from earthreport.data.denoiser import denoise_pipeline, rlc_signal
from earthreport.data.simulator import compute_stats
from earthreport.dashboard.renderer import render_dashboard


def run_pipeline(
    region_key: str = "scs",
    seed: int = 42,
    source: str = "simulated",
    llm_provider: str = "mock",
    output_dir: str = "reports",
) -> str:
    region = REGIONS[region_key]
    connector = get_connector(source)
    sim_cfg = SimConfig(seed=seed)

    print(f"[1/4] Fetching {region.name_cn} data (source={source}, seed={seed}) ...")
    metrics = connector.fetch(region, sim_cfg)
    print(f"       -> {len(metrics)} records")

    print("[2/4] Computing statistics + denoising ...")
    stats = compute_stats(metrics)
    print(f"       SST:  mean={stats['sst_mean']:.2f}°C  "
          f"range=[{stats['sst_min']:.1f}, {stats['sst_max']:.1f}]")
    print(f"       Chl-a: mean={stats['chl_mean']:.3f} mg/m³")
    print(f"       POC:  mean={stats['poc_flux_mean']:.2f} gC/m²")

    sig = rlc_signal(hours=1, sample_rate_hz=0.1, noise_sigma=0.15)
    denoised = denoise_pipeline(sig)
    print(f"       RLC denoise: SNR {denoised.snr_before:.1f} -> {denoised.snr_after:.1f} dB "
          f"(gain +{denoised.gain_db:.1f} dB)")

    print(f"[3/4] Generating AI health report (llm={llm_provider}) ...")
    llm = get_llm(llm_provider)
    generator = ReportGenerator(llm)
    report = generator.generate(
        region_cn=region.name_cn,
        sst_mean=stats["sst_mean"],
        chl_mean=stats["chl_mean"],
        chl_std=stats["chl_std"],
        poc_surface=stats["chl_mean"] * 2.5,
        poc_at_100m=stats["poc_flux_mean"],
        snr_before=denoised.snr_before,
        snr_after=denoised.snr_after,
        gain_db=denoised.gain_db,
    )
    print(f"       碳汇效率: {report.carbon.grade} | 热浪风险: {report.heatwave.grade} | "
          f"生物多样性: {report.biodiversity.grade}")

    print("[4/4] Rendering HTML report ...")
    output_path = Path(output_dir) / f"report_{region_key}_{sim_cfg.hours}h.html"
    path = render_dashboard(metrics, region, stats, output_path,
                            report=report, version=__version__)

    json_path = Path(output_dir) / f"report_{region_key}_{sim_cfg.hours}h.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
                         encoding="utf-8")

    print(f"       HTML -> {path}")
    print(f"       JSON -> {json_path}")
    return str(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="地球动态报告 — 海洋碳汇数字孪生")
    parser.add_argument("--region", default="scs",
                        choices=list(REGIONS), help="Observation region (default: scs)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    parser.add_argument("--source", default="simulated",
                        choices=["simulated", "copernicus", "argo"],
                        help="Data source (default: simulated)")
    parser.add_argument("--llm", default="mock",
                        choices=["mock", "claude", "openai"],
                        help="LLM provider (default: mock)")
    parser.add_argument("--output", default="reports",
                        help="Output directory (default: reports)")
    args = parser.parse_args()
    run_pipeline(region_key=args.region, seed=args.seed,
                 source=args.source, llm_provider=args.llm, output_dir=args.output)


if __name__ == "__main__":
    main()
