"""Data source connectors — simulated now, real APIs later."""

from __future__ import annotations

from earthreport.config import OceanMetrics, RegionConfig, SimConfig
from earthreport.data.simulator import generate_ocean_data


class DataConnector:
    def fetch(self, region: RegionConfig, config: SimConfig | None = None) -> list[OceanMetrics]:
        raise NotImplementedError


class SimulatedConnector(DataConnector):
    def fetch(self, region: RegionConfig, config: SimConfig | None = None) -> list[OceanMetrics]:
        return generate_ocean_data(region, config)


class CopernicusConnector(DataConnector):
    def fetch(self, region: RegionConfig, config: SimConfig | None = None) -> list[OceanMetrics]:
        raise NotImplementedError("Copernicus API connector not yet implemented")


class ARGOConnector(DataConnector):
    def fetch(self, region: RegionConfig, config: SimConfig | None = None) -> list[OceanMetrics]:
        raise NotImplementedError("ARGO connector not yet implemented")


def get_connector(source: str = "simulated") -> DataConnector:
    connectors: dict[str, DataConnector] = {
        "simulated": SimulatedConnector(),
        "copernicus": CopernicusConnector(),
        "argo": ARGOConnector(),
    }
    if source not in connectors:
        raise ValueError(f"Unknown data source: {source}. Available: {list(connectors)}")
    return connectors[source]
