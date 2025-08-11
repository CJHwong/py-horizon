from datetime import UTC, datetime

from horizon.l2_use_cases.boundaries.location_service import Location, LocationGateway
from horizon.l2_use_cases.boundaries.prefs_gateway import IPreferencesGateway, Preferences
from horizon.l2_use_cases.compute_sky_use_case import ComputeSkyUseCase
from horizon.l3_interface_adapters.presenters.sky_presenter import InMemorySkyPresenter


class FixedLocation(LocationGateway):
    def __init__(self, lat: float, lon: float):
        self._loc = Location(lat=lat, lon=lon)

    def current_location(self):  # type: ignore[override]
        return self._loc


class InMemoryPrefs(IPreferencesGateway):
    def __init__(self, prefs: Preferences):
        self._prefs = prefs

    def load(self):  # type: ignore[override]
        return self._prefs

    def save(self, prefs: Preferences):  # type: ignore[override]
        self._prefs = prefs


def test_minimal_mode_disables_non_astronomical_influences(monkeypatch):
    # Force multiple executions with different dates to ensure deterministic anchors unchanged by heuristics
    base_prefs = Preferences(
        influence_light_pollution=False,
        influence_weather=False,
        influence_air_quality=False,
    )
    prefs_gateway = InMemoryPrefs(base_prefs)
    presenter = InMemorySkyPresenter()
    interactor = ComputeSkyUseCase(presenter, FixedLocation(40.0, -100.0), prefs_gateway, weather=None)

    colors = set()
    for i in range(3):
        # Patch datetime.now used inside interactor to simulate different days (heuristic seed changes)
        fake_now = datetime(2025, 3, 20 + i, 12, 0, tzinfo=UTC)  # midday -> DAY regime

        class _DT:
            @staticmethod
            def now(tz=None):
                return fake_now

        monkeypatch.setattr('horizon.l2_use_cases.compute_sky_use_case.datetime', _DT)
        interactor.execute()
        vm = presenter.latest
        assert vm is not None
        colors.add((vm.horizon_hex, vm.zenith_hex))
    # With influences disabled, heuristic variation should not affect colors -> single pair
    assert len(colors) == 1
