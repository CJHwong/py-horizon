"""Open-Meteo weather provider (optional, best-effort, no API key).

Only used if explicitly constructed; network failures return None. Keeps a
simple in-memory cache for a few minutes to avoid frequent calls.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.error import URLError
from urllib.request import urlopen

from horizon.l1_entities.models import now_utc
from horizon.l2_use_cases.boundaries.weather_provider_gateway import WeatherProviderGateway, WeatherSample


@dataclass
class _CacheEntry:
    sample: WeatherSample
    expires: datetime


class OpenMeteoWeatherGateway(WeatherProviderGateway):  # pragma: no cover - network
    def __init__(self, ttl_minutes: int = 10):
        self._cache: _CacheEntry | None = None
        self._ttl = timedelta(minutes=ttl_minutes)

    def sample(self, lat: float, lon: float) -> WeatherSample | None:
        now = now_utc()
        if self._cache and self._cache.expires > now:
            return self._cache.sample
        url = (
            'https://api.open-meteo.com/v1/forecast?latitude='
            f'{lat:.3f}&longitude={lon:.3f}&current=cloud_cover,relative_humidity_2m,visibility,temperature_2m'
        )
        try:
            with urlopen(url, timeout=5) as resp:  # noqa: S310
                data = json.load(resp)
        except (URLError, TimeoutError, OSError, json.JSONDecodeError):
            return None
        current = data.get('current') or {}
        cloud_cover = (current.get('cloud_cover') or 0) / 100.0
        rel_humidity = (current.get('relative_humidity_2m') or 0) / 100.0
        visibility_m = current.get('visibility') or 0
        temperature_c = current.get('temperature_2m')
        visibility_km = visibility_m / 1000.0 if visibility_m else 0.0
        sample = WeatherSample(
            cloud_cover=max(0.0, min(1.0, cloud_cover)),
            visibility_km=visibility_km,
            rel_humidity=max(0.0, min(1.0, rel_humidity)),
            temperature_c=temperature_c,
            timestamp=now,
        )
        self._cache = _CacheEntry(sample=sample, expires=now + self._ttl)
        return sample
