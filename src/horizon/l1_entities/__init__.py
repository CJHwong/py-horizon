"""Domain entities layer."""

# Core domain models and business rules
# Atmospheric physics and environmental calculations
from .atmospheric import Heuristics, atmospheric_sky_colors, derive

# Color mathematics and visual effects
from .color import (
    Color,
    apply_air_quality_effect,
    apply_light_pollution_effect,
    apply_overcast_effect,
    apply_turbidity_effect,
    apply_weather_effects,
)
from .core import Location, SkyRegime, SkySnapshot, classify_regime, now_utc, round_coord

# Domain exceptions
from .exceptions import (
    AtmosphericCalculationError,
    ColorSpaceError,
    DomainError,
    InvalidCoordinatesError,
    PreferencesError,
    SunPositionError,
    WeatherDataError,
)

# Geographic and astronomical calculations
from .geo import SunPosition, sun_position
