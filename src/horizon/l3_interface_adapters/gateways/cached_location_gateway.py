"""Location gateway with preferences-aware fallback and caching."""

from horizon.l1_entities import round_coord
from horizon.l2_use_cases.boundaries.location_service import Location, LocationGateway
from horizon.l2_use_cases.boundaries.prefs_gateway import PreferencesGateway


class CachedLocationGateway(LocationGateway):
    """Location gateway that only uses IP location when preferences don't provide coordinates."""

    def __init__(self, inner: LocationGateway, prefs_gateway: PreferencesGateway):
        self._inner = inner
        self._prefs_gateway = prefs_gateway
        self._last: Location | None = None

    def current_location(self) -> Location | None:
        # Check if preferences provide an absolute location first
        prefs = self._prefs_gateway.load()
        if prefs.lat is not None and prefs.lon is not None:
            # Use preferences location as absolute coordinate
            precision = getattr(prefs, 'location_precision_deg', 0.25) or 0.25
            return Location(lat=round_coord(prefs.lat, precision), lon=round_coord(prefs.lon, precision))

        # Only use IP location service when prefs don't provide location
        loc = self._inner.current_location()
        if loc:
            self._last = loc
        loc = self._last
        if not loc:
            return None
        precision = getattr(prefs, 'location_precision_deg', 0.25) or 0.25
        return Location(lat=round_coord(loc.lat, precision), lon=round_coord(loc.lon, precision))
