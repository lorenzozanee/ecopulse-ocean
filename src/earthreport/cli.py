"""CLI entry point — argparse, mirrors oceanicdata-cli/main.py:54."""

from __future__ import annotations

import argparse
from pathlib import Path

from earthreport import __version__
from earthreport.config import REGIONS, SimConfig
from earthreport.data.connectors import get_connector
from earthreport.data.simulator import compute_stats
from earthreport.dashboard.renderer import render_dashboard


def run_pipeline(
    region_key: str = "scs",
    seed: int = 42,
    source: str = "simulated",
    output_dir: str = "reports",
) -> str:
    region = REGIONS[region_key]
    connector = get_connector(source)
    sim_cfg = SimConfig(seed=seed)

    print(f"[1/3] Fetching {region.name_cn} data (source={source}, seed={seed}) ...")
    metrics = connector.fetch(region, sim_cfg)
    print(f"       -> {len(metrics)} records")

    print("[2/3] Computing statistics ...")
    stats = compute_stats(metrics)
    print(f"       SST:  mean={stats['sst_mean']:.2f}°C  "
          f"range=[{stats['sst_min']:.1f}, {stats['sst_max']:.1f}]")
    print(f"       Chl-a: mean={stats['chl_mean']:.3f} mg/m³")
    print(f"       POC:  mean={stats['poc_flux_mean']:.2f} gC/m²")

    print("[3/3] Rendering HTML report ...")
    output_path = Path(output_dir) / f"report_{region_key}_{sim_cfg.hours}h.html"
    path = render_dashboard(metrics, region, stats, output_path, version=__version__)
    print(f"       -> {path}")

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
    parser.add_argument("--output", default="reports",
                        help="Output directory (default: reports)")
    args = parser.parse_args()
    run_pipeline(region_key=args.region, seed=args.seed,
                 source=args.source, output_dir=args.output)


if __name__ == "__main__":
    main()
