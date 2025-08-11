"""Solar position calculation (simplified) producing altitude & azimuth in degrees.
Pure (no side effects). Algorithm: NOAA / simplified SPA approximation adequate for sky color.
"""

import math
from dataclasses import dataclass
from datetime import UTC, datetime

# Constants
_DEG2RAD = math.pi / 180.0
_RAD2DEG = 180.0 / math.pi


@dataclass(frozen=True)
class SunPosition:
    altitude_deg: float
    azimuth_deg: float  # Degrees from North, clockwise


def _julian_day(dt: datetime) -> float:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    dt = dt.astimezone(UTC)
    y = dt.year
    m = dt.month
    d = dt.day + (dt.hour + (dt.minute + dt.second / 60.0) / 60.0) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    A = y // 100
    B = 2 - A + A // 4
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5
    return jd


def _sun_coords(jd: float) -> tuple[float, float]:
    # Based on NOAA Solar Calculator approximations
    n = jd - 2451545.0
    L = (280.46 + 0.9856474 * n) % 360  # mean longitude
    g = math.radians((357.528 + 0.9856003 * n) % 360)  # mean anomaly
    lambda_ecliptic = (L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360
    epsilon = 23.439 - 0.0000004 * n  # obliquity
    lambda_rad = math.radians(lambda_ecliptic)
    epsilon_rad = math.radians(epsilon)
    # Convert to RA/Dec
    alpha = math.atan2(math.cos(epsilon_rad) * math.sin(lambda_rad), math.cos(lambda_rad))
    delta = math.asin(math.sin(epsilon_rad) * math.sin(lambda_rad))
    return alpha, delta  # radians


def sun_position(dt: datetime, lat_deg: float, lon_deg: float) -> SunPosition:
    """Compute solar position.
    Returns approximate altitude & azimuth (deg). Accurate within ~0.5° for daily sky gradient use.
    """
    jd = _julian_day(dt)
    alpha, delta = _sun_coords(jd)
    # Sidereal time
    n = jd - 2451545.0
    theta = (280.46061837 + 360.98564736629 * n + lon_deg) % 360
    H = math.radians(theta) - alpha  # hour angle
    lat = lat_deg * _DEG2RAD
    altitude = math.asin(math.sin(lat) * math.sin(delta) + math.cos(lat) * math.cos(delta) * math.cos(H))
    azimuth = math.atan2(-math.sin(H), (math.tan(delta) * math.cos(lat) - math.sin(lat) * math.cos(H)))
    alt_deg = altitude * _RAD2DEG
    az_deg = (azimuth * _RAD2DEG + 360) % 360
    return SunPosition(altitude_deg=alt_deg, azimuth_deg=az_deg)
