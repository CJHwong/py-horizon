"""Color effect functions for atmospheric influences.

These functions apply various atmospheric effects to base sky colors
computed from the atmospheric scattering model.
"""

from .colors import Color


def apply_overcast_effect(horizon_color: Color, zenith_color: Color, overcast_factor: float) -> tuple[Color, Color]:
    """Apply overcast desaturation and contrast reduction effects.

    Args:
        horizon_color: Base horizon color from atmospheric scattering
        zenith_color: Base zenith color from atmospheric scattering
        overcast_factor: Amount of overcast (0.0 = clear, 1.0 = fully overcast)

    Returns:
        Tuple of (modified_horizon_color, modified_zenith_color)
    """
    if overcast_factor <= 0:
        return horizon_color, zenith_color

    # Desaturate both colors
    horizon = horizon_color.desaturate(overcast_factor)
    zenith = zenith_color.desaturate(overcast_factor)

    # Reduce contrast by blending toward the midpoint
    blend = overcast_factor * 0.4
    mid = horizon.lerp(zenith, 0.5)
    horizon = horizon.lerp(mid, blend)
    zenith = zenith.lerp(mid, blend)

    return horizon.clamp(), zenith.clamp()


def apply_turbidity_effect(horizon_color: Color, zenith_color: Color, turbidity_level: float) -> tuple[Color, Color]:
    """Apply turbidity warm shift effect.

    Args:
        horizon_color: Base horizon color from atmospheric scattering
        zenith_color: Base zenith color from atmospheric scattering
        turbidity_level: Turbidity value (2.2 = clear, 3.0 = hazy)

    Returns:
        Tuple of (modified_horizon_color, modified_zenith_color)
    """
    # Normalize turbidity to 0..1 range (2.2 -> 0, 3.0 -> 1)
    warm = max(0.0, (turbidity_level - 2.2) / 0.8)

    if warm <= 0:
        return horizon_color, zenith_color

    # For deep night conditions (pure black colors), turbidity has minimal effect
    # since there's no sunlight to scatter through atmospheric particles
    base_luminance = 0.2126 * zenith_color.r + 0.7152 * zenith_color.g + 0.0722 * zenith_color.b
    night_attenuation = min(1.0, base_luminance * 10)  # Strong attenuation when very dark

    # Apply red boost to horizon (primary effect)
    horizon = Color(horizon_color.r + 0.08 * warm * night_attenuation, horizon_color.g, horizon_color.b).clamp()

    # Zenith gets minimal warming, heavily attenuated during night
    zenith = Color(zenith_color.r + 0.03 * warm * night_attenuation, zenith_color.g, zenith_color.b).clamp()

    return horizon, zenith


def apply_light_pollution_effect(
    horizon_color: Color, zenith_color: Color, pollution_level: float
) -> tuple[Color, Color]:
    """Apply light pollution effects (urban glow, color shift).

    Light pollution creates a dramatic dome effect where the horizon glows orange/amber
    from streetlights while the zenith remains completely dark during deep night.

    Args:
        horizon_color: Base horizon color from atmospheric scattering
        zenith_color: Base zenith color from atmospheric scattering
        pollution_level: Light pollution intensity (0.0 = rural, 1.0 = urban)

    Returns:
        Tuple of (modified_horizon_color, modified_zenith_color)
    """
    if pollution_level <= 0:
        return horizon_color, zenith_color

    # Light pollution creates orange/amber glow near horizon
    pollution_color = Color(1.0, 0.65, 0.35)  # Warmer amber, more realistic

    # Check if we're in deep night conditions
    base_luminance = 0.2126 * zenith_color.r + 0.7152 * zenith_color.g + 0.0722 * zenith_color.b

    # During deep night, light pollution creates a dramatic dome effect
    if base_luminance < 0.01:  # Deep night threshold
        # Zenith remains completely unaffected - light pollution doesn't reach straight up
        zenith_blend = 0.0
        # Horizon gets stronger effect to create dramatic contrast
        horizon_blend = pollution_level * 0.18  # Increased from 0.15
    else:
        # During twilight/day, more uniform but still horizon-focused
        zenith_blend = pollution_level * 0.03  # Reduced from 0.05
        horizon_blend = pollution_level * 0.12  # Slightly reduced for twilight balance

    horizon = horizon_color.lerp(pollution_color, horizon_blend).clamp()
    zenith = zenith_color.lerp(pollution_color, zenith_blend).clamp()

    return horizon, zenith


def apply_weather_effects(
    horizon_color: Color, zenith_color: Color, cloud_cover: float, humidity: float | None = None
) -> tuple[Color, Color]:
    """Apply weather-based color modifications.

    Args:
        horizon_color: Base horizon color from atmospheric scattering
        zenith_color: Base zenith color from atmospheric scattering
        cloud_cover: Cloud coverage (0.0 = clear, 1.0 = fully cloudy)
        humidity: Relative humidity (0.0 to 1.0), optional

    Returns:
        Tuple of (modified_horizon_color, modified_zenith_color)
    """
    # Weather effects primarily handled through overcast factor
    # But we can add subtle humidity-based haze effects
    if humidity is not None and humidity > 0.7:
        # High humidity creates slight haze effect
        haze_factor = min(0.1, (humidity - 0.7) * 0.3)
        # Slightly desaturate and warm colors
        horizon = horizon_color.desaturate(haze_factor * 0.3)
        zenith = zenith_color.desaturate(haze_factor * 0.2)
        # Add slight warm tint
        warm_tint = Color(1.05, 1.0, 0.95)
        horizon = Color(horizon.r * warm_tint.r, horizon.g * warm_tint.g, horizon.b * warm_tint.b).clamp()
        zenith = Color(zenith.r * warm_tint.r, zenith.g * warm_tint.g, zenith.b * warm_tint.b).clamp()
        return horizon, zenith

    return horizon_color, zenith_color


def apply_air_quality_effect(horizon_color: Color, zenith_color: Color, aqi: int | None) -> tuple[Color, Color]:
    """Apply air quality effects (haze, color shift based on pollution).

    Args:
        horizon_color: Base horizon color from atmospheric scattering
        zenith_color: Base zenith color from atmospheric scattering
        aqi: Air Quality Index (0-500 scale), optional

    Returns:
        Tuple of (modified_horizon_color, modified_zenith_color)
    """
    if aqi is None or aqi <= 50:  # Good air quality
        return horizon_color, zenith_color

    # Normalize AQI to 0..1 effect strength (50 -> 0, 300+ -> 1)
    effect_strength = min(1.0, max(0.0, (aqi - 50) / 250))

    # Poor air quality creates brown/gray haze
    if aqi <= 150:  # Moderate to unhealthy
        haze_color = Color(0.8, 0.7, 0.6)  # Brown haze
    else:  # Very unhealthy+
        haze_color = Color(0.6, 0.6, 0.5)  # Gray haze

    # For deep night conditions, air quality effects are less visible
    # since there's minimal light to scatter through the particulates
    base_luminance = 0.2126 * zenith_color.r + 0.7152 * zenith_color.g + 0.0722 * zenith_color.b

    # During deep night, significantly reduce air quality effects
    if base_luminance < 0.01:  # Deep night threshold
        night_attenuation = 0.05  # Reduce effect to 5% during deep night
    else:
        night_attenuation = 1.0

    # Apply haze effect, stronger at horizon, attenuated during night
    horizon_blend = effect_strength * 0.2 * night_attenuation
    zenith_blend = effect_strength * 0.1 * night_attenuation

    horizon = horizon_color.lerp(haze_color, horizon_blend).clamp()
    zenith = zenith_color.lerp(haze_color, zenith_blend).clamp()

    return horizon, zenith


__all__ = [
    'apply_overcast_effect',
    'apply_turbidity_effect',
    'apply_light_pollution_effect',
    'apply_weather_effects',
    'apply_air_quality_effect',
]
