"""Optional weather provider boundary (returns real data if configured)."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class WeatherSample:
    cloud_cover: float  # 0..1
    visibility_km: float
    rel_humidity: float  # 0..1
    timestamp: datetime
    temperature_c: float | None = None


class WeatherProviderGateway(Protocol):
    def sample(self, lat: float, lon: float) -> WeatherSample | None: ...
