from collections.abc import Iterable

from horizon.l2_use_cases.boundaries.location_service import Location, LocationGateway
from horizon.l2_use_cases.boundaries.prefs_gateway import Preferences, PreferencesGateway
from horizon.l3_interface_adapters.gateways.cached_location_gateway import CachedLocationGateway


class DummyLocation(LocationGateway):
    def __init__(self, seq: Iterable) -> None:
        self._seq = iter(seq)

    def current_location(self) -> Location | None:
        try:
            return next(self._seq)
        except StopIteration:
            return None


class DummyPrefsGateway(PreferencesGateway):
    def __init__(self, prefs: Preferences):
        self._prefs = prefs

    def load(self) -> Preferences:
        return self._prefs

    def save(self, prefs: Preferences) -> None:
        self._prefs = prefs


def test_cached_rounding_and_sticky() -> None:
    """Test that when prefs don't have location, IP location is used with rounding and caching."""
    prefs = Preferences(location_precision_deg=1.0)  # coarse rounding 1 degree, no lat/lon
    prefs_gateway = DummyPrefsGateway(prefs)
    inner = DummyLocation([Location(10.4, 20.6)])
    svc = CachedLocationGateway(inner, prefs_gateway)
    loc1 = svc.current_location()
    assert loc1 == Location(lat=10.0, lon=21.0)
    # underlying iterator exhausted; should still return cached rounded value
    loc2 = svc.current_location()
    assert loc2 == loc1


def test_prefs_location_overrides_ip() -> None:
    """Test that when prefs have location, they are used instead of IP location."""
    prefs = Preferences(lat=37.7749, lon=-122.4194, location_precision_deg=0.25)
    prefs_gateway = DummyPrefsGateway(prefs)
    inner = DummyLocation([Location(10.4, 20.6)])  # This should be ignored
    svc = CachedLocationGateway(inner, prefs_gateway)
    loc = svc.current_location()
    # Should use prefs location, rounded to 0.25 precision
    assert loc == Location(lat=37.75, lon=-122.5)


def test_no_location_fallback() -> None:
    """Test that when prefs don't have location and IP fails, None is returned."""
    prefs = Preferences(location_precision_deg=1.0)  # no lat/lon
    prefs_gateway = DummyPrefsGateway(prefs)
    inner = DummyLocation([])  # empty sequence, will return None
    svc = CachedLocationGateway(inner, prefs_gateway)
    loc = svc.current_location()
    assert loc is None
