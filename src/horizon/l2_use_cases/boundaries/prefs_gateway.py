"""Preferences gateway boundary."""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Preferences:
    lat: float | None = None
    lon: float | None = None
    update_seconds: int = 60
    location_precision_deg: float = 0.25  # rounding granularity for privacy
    exact_time: str | None = None  # ISO format datetime string to override current time
    # Influence toggles controlling which non-astronomical factors affect colors
    influence_light_pollution: bool = True
    influence_weather: bool = True  # Controls overcast, turbidity adjustments, and weather effects
    influence_air_quality: bool = True


class IPreferencesGateway(Protocol):
    def load(self) -> Preferences: ...
    def save(self, prefs: Preferences) -> None: ...
