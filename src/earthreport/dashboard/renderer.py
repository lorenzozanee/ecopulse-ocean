"""Jinja2 HTML dashboard renderer — mirrors oceanicdata-cli pattern."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Template

from earthreport.config import OceanMetrics, RegionConfig

if TYPE_CHECKING:
    from earthreport.analyst.report import HealthReport

DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>地球动态报告 — {{ region.name_cn }}</title>
<style>
  :root {
    --bg: #060b10; --surface: #0d1520; --border: #1a2a3a;
    --accent: #00d4ff; --warn: #ff9100; --danger: #ff3d71;
    --text: #8899aa; --text-bright: #ccdde8;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--bg); color:var(--text); font-family:monospace; padding:20px; }
  h1 { color:var(--accent); font-size:1.2rem; margin-bottom:4px; }
  .subtitle { color:#556677; font-size:0.7rem; margin-bottom:20px; }

  .stats-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; margin-bottom:20px; }
  .stat-card {
    background:var(--surface); border:1px solid var(--border); border-radius:6px; padding:14px;
  }
  .stat-card .value { font-size:1.4rem; font-weight:700; }
  .stat-card .label { font-size:0.6rem; color:#556677; margin-top:4px; text-transform:uppercase; }
  .stat-card .range { font-size:0.6rem; color:#445566; margin-top:2px; }

  .chart { background:var(--surface); border:1px solid var(--border); border-radius:6px; padding:16px; margin-bottom:16px; }
  .chart h3 { font-size:0.7rem; color:var(--accent); margin-bottom:10px; }

  table { width:100%; border-collapse:collapse; font-size:0.68rem; }
  th, td { padding:6px 10px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.04); }
  th { color:var(--accent); font-weight:600; }
  tr:hover td { background:rgba(255,255,255,0.02); }

  .footer { font-size:0.6rem; color:#445566; margin-top:24px; text-align:center; }
</style>
</head>
<body>
<h1>地球动态报告 — {{ region.name_cn }} ({{ region.name.upper() }})</h1>
<div class="subtitle">
  坐标: {{ region.lat_min }}°–{{ region.lat_max }}°N, {{ region.lon_min }}°–{{ region.lon_max }}°E |
  时间跨度: {{ metrics[0].timestamp[:10] }} ({{ metrics|length }} 时间步长) |
  生成时间: {{ generated_at }}
</div>

<div class="stats-grid">
  {% for card in stat_cards %}
  <div class="stat-card">
    <div class="value" style="color:{{ card.color }}">{{ card.value }}</div>
    <div class="label">{{ card.label }}</div>
    <div class="range">范围: {{ card.range }}</div>
  </div>
  {% endfor %}
</div>

<div class="chart">
  <h3>AI 地球健康评估</h3>
  {% for section in report_sections %}
  <div style="background:rgba(0,0,0,0.2); border:1px solid var(--border); border-radius:5px; padding:10px; margin-bottom:8px;">
    <h4 style="font-size:0.68rem; color:var(--accent); margin-bottom:4px;">
      {{ section.title }}
      {% if section.grade %}
      <span style="display:inline-block; padding:1px 7px; border-radius:3px; font-weight:700; font-size:0.72rem;
        {% if section.grade == 'A' %}background:rgba(76,175,80,0.2);color:#4caf50;
        {% elif section.grade == 'B' %}background:rgba(255,193,7,0.2);color:#ffc107;
        {% elif section.grade == 'C' %}background:rgba(255,145,0,0.2);color:#ff9100;
        {% else %}background:rgba(255,61,113,0.2);color:#ff3d71;{% endif %}">
        {{ section.grade }}
      </span>
      {% endif %}
    </h4>
    <p style="font-size:0.64rem; line-height:1.45; color:#778899;">{{ section.narrative }}</p>
  </div>
  {% endfor %}
</div>

<div class="chart">
  <h3>观测时序数据 (前 12 行)</h3>
  <table>
    <thead>
      <tr><th>时间</th><th>SST (°C)</th><th>Chl-a (mg/m³)</th><th>POC通量 (gC/m²)</th><th>MLD (m)</th><th>盐度 (PSU)</th></tr>
    </thead>
    <tbody>
      {% for m in metrics[:12] %}
      <tr>
        <td>{{ m.timestamp[11:19] }}</td>
        <td>{{ m.sst }}</td>
        <td>{{ m.chl }}</td>
        <td>{{ m.poc_flux }}</td>
        <td>{{ m.mld }}</td>
        <td>{{ m.salinity }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

<div class="footer">
  EcoPulse-Ocean / 蓝碳脉搏 — 地球动态报告 v{{ version }} | 数据源: 模拟引擎
</div>
</body>
</html>"""


def render_dashboard(
    metrics: list[OceanMetrics],
    region: RegionConfig,
    stats: dict[str, float],
    output_path: Path,
    report: HealthReport | None = None,
    version: str = "0.1.0",
) -> Path:
    template = Template(DASHBOARD_TEMPLATE)

    stat_cards = [
        {"color": "#00d4ff", "value": f"{stats['sst_mean']:.1f}°C",
         "label": "Average SST", "range": f"{stats['sst_min']:.1f}–{stats['sst_max']:.1f}"},
        {"color": "#66bb6a", "value": f"{stats['chl_mean']:.3f} mg/m³",
         "label": "Average Chl-a", "range": f"{stats['chl_min']:.3f}–{stats['chl_max']:.3f}"},
        {"color": "#ffb74d", "value": f"{stats['poc_flux_mean']:.2f} gC/m²",
         "label": "Average POC Flux", "range": f"{stats['poc_flux_min']:.2f}–{stats['poc_flux_max']:.2f}"},
        {"color": "#ce93d8", "value": f"{stats['mld_mean']:.1f} m",
         "label": "Average MLD", "range": f"{stats['mld_min']:.1f}–{stats['mld_max']:.1f}"},
        {"color": "#80cbc4", "value": f"{stats['salinity_mean']:.3f} PSU",
         "label": "Average Salinity", "range": f"{stats['salinity_min']:.3f}–{stats['salinity_max']:.3f}"},
    ]

    report_sections = report.to_dict()["sections"] if report else []

    html = template.render(
        region=region,
        metrics=metrics,
        stat_cards=stat_cards,
        report_sections=report_sections,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        version=version,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path
