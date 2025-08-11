"""Sky regime classification based on solar altitude."""

from enum import Enum


class SkyRegime(str, Enum):
    DAY = 'DAY'
    LOW_SUN = 'LOW_SUN'
    CIVIL = 'CIVIL'
    NAUTICAL = 'NAUTICAL'
    ASTRONOMICAL = 'ASTRONOMICAL'
    NIGHT = 'NIGHT'


def classify_regime(altitude_deg: float) -> SkyRegime:
    if altitude_deg >= 10:
        return SkyRegime.DAY
    if altitude_deg >= 0:
        return SkyRegime.LOW_SUN
    if altitude_deg >= -6:
        return SkyRegime.CIVIL
    if altitude_deg >= -12:
        return SkyRegime.NAUTICAL
    if altitude_deg >= -18:
        return SkyRegime.ASTRONOMICAL
    return SkyRegime.NIGHT
