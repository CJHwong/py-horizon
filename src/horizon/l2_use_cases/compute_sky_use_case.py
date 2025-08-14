"""ComputeSky interactor."""

from dataclasses import dataclass
from datetime import UTC, datetime

from horizon.l1_entities import (
    Heuristics,
    SkySnapshot,
    apply_air_quality_effect,
    apply_light_pollution_effect,
    apply_overcast_effect,
    apply_turbidity_effect,
    apply_weather_effects,
    atmospheric_sky_colors,
    classify_regime,
    derive,
    sun_position,
)

from .boundaries.location_service import LocationGateway
from .boundaries.prefs_gateway import PreferencesGateway
from .boundaries.presenter import SkyPresenter
from .boundaries.weather_provider_gateway import WeatherProviderGateway


class ComputeSkyUseCase:
    def __init__(
        self,
        presenter: SkyPresenter,
        location_service: LocationGateway,
        prefs: PreferencesGateway,
        weather: WeatherProviderGateway | None = None,
    ):
        self.presenter = presenter
        self.location_service = location_service
        self.prefs_gateway = prefs
        self.weather = weather

    def execute(self) -> None:
        prefs = self.prefs_gateway.load()

        # Use exact_time if specified, otherwise use current time
        now = datetime.now(UTC)
        if prefs.exact_time:
            try:
                # Support simple HH:MM format (assumes today's date)
                if ':' in prefs.exact_time and 'T' not in prefs.exact_time:
                    today = datetime.now(UTC).date()
                    time_str = f'{today.isoformat()}T{prefs.exact_time}:00Z'
                    now = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                else:
                    # Full ISO format
                    now = datetime.fromisoformat(prefs.exact_time.replace('Z', '+00:00'))

                if now.tzinfo is None:
                    now = now.replace(tzinfo=UTC)
            except (ValueError, AttributeError):
                pass

        loc = self.location_service.current_location()
        if loc:
            lat = loc.lat
            lon = loc.lon
        else:
            # Ultimate fallback if location service returns None
            # Default to coordinates in Taipei, Taiwan
            lat = 25.105497
            lon = 121.597366

        # Round for privacy/determinism using configured precision
        precision = getattr(prefs, 'location_precision_deg', 0.25) or 0.25
        if precision <= 0:
            precision = 0.25
        inv = 1.0 / precision
        lat_round = round(lat * inv) / inv
        lon_round = round(lon * inv) / inv
        sun = sun_position(now, lat_round, lon_round)
        regime = classify_regime(sun.altitude_deg)

        # Always start with atmospheric scattering as the base
        horizon, zenith = atmospheric_sky_colors(sun.altitude_deg)
        # Derive heuristics for effect application
        heur = derive(lat_round, lon_round, now)

        # Apply atmospheric effects based on influence toggles
        # Each effect is applied only if its influence toggle is enabled

        # 1. Light pollution effects (always available from heuristics)
        if getattr(prefs, 'influence_light_pollution', True) and heur.light_pollution > 0:
            horizon, zenith = apply_light_pollution_effect(horizon, zenith, heur.light_pollution)

        # 2. Weather data collection and effects
        temperature_c: float | None = None
        weather_summary: str | None = None
        cloud_cover = heur.overcast  # Default to heuristic overcast
        humidity = None

        # Apply baseline turbidity from heuristics
        baseline_turbidity = heur.turbidity
        if getattr(prefs, 'influence_weather', True):
            horizon, zenith = apply_turbidity_effect(horizon, zenith, baseline_turbidity)

        if self.weather:
            sample = self.weather.sample(lat_round, lon_round)
            if sample:
                # Always collect weather data for display
                temperature_c = sample.temperature_c
                weather_summary = 'Clouds' if sample.cloud_cover > 0.5 else 'Clear'

                # Only apply weather effects if influence toggle is enabled
                if getattr(prefs, 'influence_weather', True):
                    cloud_cover = sample.cloud_cover
                    humidity = sample.rel_humidity

                    # Apply weather-specific effects
                    horizon, zenith = apply_weather_effects(horizon, zenith, cloud_cover, humidity)

                    # Apply overcast effect using actual weather data
                    if cloud_cover > 0:
                        horizon, zenith = apply_overcast_effect(horizon, zenith, cloud_cover)

                    # Update turbidity with humidity adjustment
                    adjusted_turbidity = _adjust_turbidity_with_humidity(baseline_turbidity, humidity)
                    if adjusted_turbidity != baseline_turbidity:
                        # Re-apply turbidity effect with adjusted value
                        horizon, zenith = apply_turbidity_effect(horizon, zenith, adjusted_turbidity)
                        heur = type(heur)(
                            turbidity=adjusted_turbidity,
                            overcast=heur.overcast,
                            light_pollution=heur.light_pollution,
                        )

        # 3. Air quality effects
        air_quality_index = _derive_aqi(heur)
        if getattr(prefs, 'influence_air_quality', True):
            horizon, zenith = apply_air_quality_effect(horizon, zenith, air_quality_index)
        # Compute final colors and snapshot
        avg = horizon.lerp(zenith, 0.5)
        snapshot = SkySnapshot(
            lat_deg=lat_round,
            lon_deg=lon_round,
            sun=sun,
            regime=regime,
            horizon=horizon,
            zenith=zenith,
            avg=avg,
            heuristics=heur,
            temperature_c=temperature_c,
            weather_summary=weather_summary,
            air_quality_index=air_quality_index,
        )
        self.presenter.present(snapshot)


def _adjust_turbidity_with_humidity(base_t: float, rh: float | None) -> float:
    if rh is None:
        return base_t
    if rh > 0.7:
        boost = min(0.5, (rh - 0.7) * 1.2)
        return min(3.2, base_t + boost)
    return base_t


def _derive_aqi(heur: Heuristics) -> int:
    """Synthetic AQI placeholder.

    Based on turbidity (proxy for particulates) and light pollution (proxy for urban NOx/ozone precursors).
    Scales roughly into EPA-style 0-500 range but is intentionally heuristic and offline.
    """
    # Normalize turbidity (2.0-3.2) -> 0..1
    t_norm = max(0.0, min(1.0, (heur.turbidity - 2.0) / 1.2))
    lp_norm = max(0.0, min(1.0, heur.light_pollution))
    # Weight turbidity higher
    raw = (t_norm * 0.7 + lp_norm * 0.3) * 300  # up to ~300 typical
    # Add overcast penalty reducing AQI slightly (rain/clouds can scavenge particulates)
    raw *= 1.0 - 0.2 * heur.overcast
    return int(max(0, min(500, round(raw))))


@dataclass
class ComputeSkyResponse:
    """Response object containing computed sky data and metadata."""

    snapshot: SkySnapshot | None
    success: bool
    error_message: str | None = None

    @classmethod
    def success_response(cls, snapshot: SkySnapshot) -> 'ComputeSkyResponse':
        """Create a successful response."""
        return cls(snapshot=snapshot, success=True, error_message=None)

    @classmethod
    def error_response(cls, error_message: str) -> 'ComputeSkyResponse':
        """Create an error response."""
        return cls(snapshot=None, success=False, error_message=error_message)


@dataclass
class ComputeSkyRequest:
    """Request object for computing sky colors."""

    # Optional overrides for location and time
    lat: float | None = None
    lon: float | None = None
    override_time: datetime | None = None

    # Optional preference overrides
    location_precision_deg: float | None = None
    influence_light_pollution: bool | None = None
    influence_weather: bool | None = None
    influence_air_quality: bool | None = None
