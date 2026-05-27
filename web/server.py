"""FastAPI server + WebSocket real-time dashboard.

Mirrors HydroSim2D/web/server.py architecture.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from earthreport import __version__
from earthreport.analyst.llm import get_llm
from earthreport.analyst.report import ReportGenerator
from earthreport.config import REGIONS, SimConfig
from earthreport.data.connectors import get_connector
from earthreport.data.denoiser import denoise_pipeline, rlc_signal
from earthreport.data.simulator import compute_stats

app = FastAPI(title="Earth Dynamic Report", version=__version__)

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
TEMPLATES_DIR = ROOT / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    template_path = TEMPLATES_DIR / "dashboard.html"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return "<h1>Dashboard template not found</h1>"


@app.get("/api/regions")
async def list_regions() -> dict:
    return {
        "regions": [
            {"key": k, "name": v.name, "name_cn": v.name_cn,
             "lat": [v.lat_min, v.lat_max], "lon": [v.lon_min, v.lon_max]}
            for k, v in REGIONS.items()
        ]
    }


@app.get("/api/report/{region_key}")
async def get_report(region_key: str, llm_provider: str = "mock") -> dict:
    if region_key not in REGIONS:
        return {"error": f"Unknown region: {region_key}"}

    region = REGIONS[region_key]
    connector = get_connector("simulated")
    metrics = connector.fetch(region, SimConfig(seed=42))
    stats = compute_stats(metrics)

    sig = rlc_signal(hours=1, sample_rate_hz=0.1, noise_sigma=0.15)
    denoised = denoise_pipeline(sig)

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

    return {
        "region": region_key,
        "region_cn": region.name_cn,
        "stats": stats,
        "report": report.to_dict(),
        "rlc": {
            "snr_before": denoised.snr_before,
            "snr_after": denoised.snr_after,
            "gain_db": denoised.gain_db,
        },
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    region_key = "scs"
    connector = get_connector("simulated")
    step = 0

    try:
        while True:
            try:
                data = await asyncio.wait_for(ws.receive_text(), timeout=0.05)
                msg = json.loads(data)
                if msg.get("type") == "set_region" and msg.get("region") in REGIONS:
                    region_key = msg["region"]
                    step = 0
            except asyncio.TimeoutError:
                pass

            region = REGIONS[region_key]
            metrics = connector.fetch(region, SimConfig(seed=42 + step))
            stats = compute_stats(metrics)
            n = len(metrics)
            current = metrics[step % n]

            await ws.send_json({
                "type": "metrics",
                "region": region_key,
                "region_cn": region.name_cn,
                "timestamp": current.timestamp,
                "sst": current.sst,
                "chl": current.chl,
                "poc_flux": current.poc_flux,
                "mld": current.mld,
                "salinity": current.salinity,
                "stats": stats,
            })
            step += 1
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        pass


def main() -> None:
    import uvicorn
    uvicorn.run("web.server:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
