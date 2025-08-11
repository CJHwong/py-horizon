"""IP-based location service using ip-api.com (free, no API key required)."""

import json
from urllib.error import URLError
from urllib.request import urlopen

from horizon.l2_use_cases.boundaries.location_service import Location, LocationGateway
from horizon.l2_use_cases.boundaries.prefs_gateway import Preferences


class IPLocationGateway(LocationGateway):
    """IP-based geolocation using ip-api.com free service."""

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    def current_location(self) -> Location | None:
        """Get location based on public IP address."""
        try:
            with urlopen('http://ip-api.com/json', timeout=self.timeout) as response:
                if response.status != 200:
                    return None

                data = json.loads(response.read().decode('utf-8'))

                if data.get('status') != 'success':
                    return None

                lat = data.get('lat')
                lon = data.get('lon')

                if lat is None or lon is None:
                    return None

                return Location(lat=float(lat), lon=float(lon))

        except (URLError, ValueError, KeyError):
            return None


class CachedLocationService(LocationGateway):
    """Decorator adding caching and precision rounding."""

    def __init__(self, inner: LocationGateway, prefs: Preferences):
        self._inner = inner
        self._prefs = prefs
        self._last: Location | None = None

    def current_location(self) -> Location | None:
        loc = self._inner.current_location()
        if loc:
            self._last = loc
        loc = self._last
        if not loc:
            return None
        precision = getattr(self._prefs, 'location_precision_deg', 0.25) or 0.25
        inv = 1.0 / precision
        return Location(lat=round(loc.lat * inv) / inv, lon=round(loc.lon * inv) / inv)
