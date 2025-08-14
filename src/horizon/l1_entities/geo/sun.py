"""Solar position calculation (simplified) producing altitude & azimuth in degrees.
Pure (no side effects). Algorithm: Based on https://aa.quae.nl/en/reken/zonpositie.html formulas
"""

import math
from dataclasses import dataclass
from datetime import UTC, datetime

# Constants
_DEG2RAD = math.pi / 180.0
_RAD2DEG = 180.0 / math.pi

# Julian day
_DAY_MS = 1000 * 60 * 60 * 24
_J1970 = 2440588
_J2000 = 2451545

# Obliquity of the Earth
_OBLIQUITY = _DEG2RAD * 23.4397


@dataclass(frozen=True)
class SunPosition:
    altitude_deg: float
    azimuth_deg: float  # Degrees from North, clockwise


def _to_julian(dt: datetime) -> float:
    """Convert datetime to Julian day number"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    dt = dt.astimezone(UTC)
    return dt.timestamp() * 1000 / _DAY_MS - 0.5 + _J1970


def _to_days(dt: datetime) -> float:
    """Convert datetime to days since J2000"""
    return _to_julian(dt) - _J2000


def _solar_mean_anomaly(d: float) -> float:
    """Solar mean anomaly"""
    return _DEG2RAD * (357.5291 + 0.98560028 * d)


def _ecliptic_longitude(M: float) -> float:
    """Ecliptic longitude with equation of center"""
    # Equation of center
    C = _DEG2RAD * (1.9148 * math.sin(M) + 0.02 * math.sin(2 * M) + 0.0003 * math.sin(3 * M))
    # Perihelion of the Earth
    P = _DEG2RAD * 102.9372
    return M + C + P + math.pi


def _right_ascension(ecliptic_lon: float, b: float) -> float:
    """Right ascension"""
    return math.atan2(
        math.sin(ecliptic_lon) * math.cos(_OBLIQUITY) - math.tan(b) * math.sin(_OBLIQUITY), math.cos(ecliptic_lon)
    )


def _declination(ecliptic_lon: float, b: float) -> float:
    """Declination"""
    return math.asin(math.sin(b) * math.cos(_OBLIQUITY) + math.cos(b) * math.sin(_OBLIQUITY) * math.sin(ecliptic_lon))


def _sun_coords(d: float) -> tuple[float, float]:
    """Sun coordinates: right ascension and declination"""
    M = _solar_mean_anomaly(d)
    L = _ecliptic_longitude(M)
    return _right_ascension(L, 0), _declination(L, 0)


def _sidereal_time(d: float, lw: float) -> float:
    """Sidereal time"""
    return _DEG2RAD * (280.16 + 360.9856235 * d) - lw


def _altitude(H: float, phi: float, dec: float) -> float:
    """Altitude calculation"""
    return math.asin(math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(H))


def _azimuth(H: float, phi: float, dec: float) -> float:
    """Azimuth calculation"""
    return math.atan2(math.sin(H), math.cos(H) * math.sin(phi) - math.tan(dec) * math.cos(phi))


def sun_position(dt: datetime, lat_deg: float, lon_deg: float) -> SunPosition:
    """Compute solar position.
    Returns approximate altitude & azimuth (deg).
    """
    lw = _DEG2RAD * -lon_deg  # longitude west (negative of longitude)
    phi = _DEG2RAD * lat_deg  # latitude in radians
    d = _to_days(dt)  # days since J2000

    # Get sun coordinates
    ra, dec = _sun_coords(d)

    # Calculate hour angle
    H = _sidereal_time(d, lw) - ra

    # Calculate altitude and azimuth
    alt_rad = _altitude(H, phi, dec)
    az_rad = _azimuth(H, phi, dec)

    # Convert to degrees
    alt_deg = alt_rad * _RAD2DEG
    az_deg = (az_rad * _RAD2DEG + 360) % 360  # Ensure positive azimuth

    return SunPosition(altitude_deg=alt_deg, azimuth_deg=az_deg)
