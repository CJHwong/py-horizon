"""Presenter producing a simple view model (stored internally)."""

from dataclasses import dataclass

from horizon.l1_entities.models import SkySnapshot
from horizon.l2_use_cases.boundaries.presenter import ISkyPresenter


@dataclass
class SkyViewModel:
    horizon_hex: str
    zenith_hex: str
    avg_hex: str
    regime: str
    lat_deg: float
    lon_deg: float
    light_pollution: float
    overcast: float
    turbidity: float
    # Optional weather (may be None / not yet integrated)
    temperature_c: float | None = None
    weather_summary: str | None = None
    air_quality_index: int | None = None


class InMemorySkyPresenter(ISkyPresenter):
    def __init__(self) -> None:
        self.latest: SkyViewModel | None = None

    def present(self, snapshot: SkySnapshot) -> None:
        self.latest = SkyViewModel(
            horizon_hex=snapshot.horizon.to_srgb_hex(),
            zenith_hex=snapshot.zenith.to_srgb_hex(),
            avg_hex=snapshot.avg.to_srgb_hex(),
            regime=snapshot.regime.value,
            lat_deg=snapshot.lat_deg,
            lon_deg=snapshot.lon_deg,
            light_pollution=snapshot.heuristics.light_pollution,
            overcast=snapshot.heuristics.overcast,
            turbidity=snapshot.heuristics.turbidity,
            temperature_c=snapshot.temperature_c,
            weather_summary=snapshot.weather_summary,
            air_quality_index=snapshot.air_quality_index,
        )
