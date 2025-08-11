"""Aggregate domain models and utility functions."""

from dataclasses import dataclass
from datetime import UTC, datetime

from .colors import Color
from .heuristics import Heuristics
from .regimes import SkyRegime
from .sun import SunPosition


@dataclass(frozen=True)
class SkySnapshot:
    lat_deg: float
    lon_deg: float
    sun: SunPosition
    regime: SkyRegime
    horizon: Color
    zenith: Color
    avg: Color
    heuristics: Heuristics
    # Optional enriched data
    temperature_c: float | None = None
    weather_summary: str | None = None
    air_quality_index: int | None = None


# Entity utility functions


def round_coord(value: float, step: float = 0.25) -> float:
    """Round geographic coordinate to specified precision."""
    return round(value / step) * step


def now_utc() -> datetime:
    """Get current UTC time."""
    return datetime.now(UTC)
