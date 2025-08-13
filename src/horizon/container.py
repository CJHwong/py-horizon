"""Dependency injection container for clean composition root."""

from collections.abc import Callable
from pathlib import Path

from horizon.l2_use_cases.boundaries.location_service import LocationGateway
from horizon.l2_use_cases.boundaries.prefs_gateway import PreferencesGateway
from horizon.l2_use_cases.boundaries.presenter import SkyPresenter
from horizon.l2_use_cases.boundaries.weather_provider_gateway import WeatherProviderGateway
from horizon.l2_use_cases.compute_sky_use_case import ComputeSkyUseCase
from horizon.l3_interface_adapters.gateways.cached_location_gateway import CachedLocationGateway
from horizon.l3_interface_adapters.gateways.ip_location_gateway import IPLocationGateway
from horizon.l3_interface_adapters.gateways.json_prefs_gateway import JsonPreferencesGateway
from horizon.l3_interface_adapters.gateways.open_meteo_weather_gateway import OpenMeteoWeatherGateway
from horizon.l3_interface_adapters.presenters.sky_presenter import InMemorySkyPresenter
from horizon.l4_frameworks_and_drivers.menu_app import MenuApp
from horizon.l4_frameworks_and_drivers.scheduler import RepeatingScheduler


class AppContainer:
    """Dependency injection container that manages application dependencies."""

    def __init__(self, prefs_file_path: Path | str = 'prefs.json'):
        self.prefs_file_path = Path(prefs_file_path)
        self._prefs_gateway: PreferencesGateway | None = None
        self._presenter: SkyPresenter | None = None
        self._location_service: LocationGateway | None = None
        self._weather_service: WeatherProviderGateway | None = None
        self._use_case: ComputeSkyUseCase | None = None

    @property
    def prefs_gateway(self) -> PreferencesGateway:
        """Get or create preferences gateway."""
        if self._prefs_gateway is None:
            self._prefs_gateway = JsonPreferencesGateway(self.prefs_file_path)
        return self._prefs_gateway

    @property
    def presenter(self) -> SkyPresenter:
        """Get or create presenter."""
        if self._presenter is None:
            self._presenter = InMemorySkyPresenter()
        return self._presenter

    @property
    def location_service(self) -> LocationGateway:
        """Get or create location service."""
        if self._location_service is None:
            ip_gateway = IPLocationGateway()
            self._location_service = CachedLocationGateway(ip_gateway, self.prefs_gateway)
        return self._location_service

    @property
    def weather_service(self) -> WeatherProviderGateway:
        """Get or create weather service."""
        if self._weather_service is None:
            self._weather_service = OpenMeteoWeatherGateway()
        return self._weather_service

    @property
    def use_case(self) -> ComputeSkyUseCase:
        """Get or create compute sky use case."""
        if self._use_case is None:
            self._use_case = ComputeSkyUseCase(
                presenter=self.presenter,
                location_service=self.location_service,
                prefs=self.prefs_gateway,
                weather=self.weather_service,
            )
        return self._use_case

    def create_menu_app(self, on_prefs_changed: Callable[[], None] | None = None) -> MenuApp:
        """Create menu app with proper dependencies."""
        return MenuApp(
            prefs_gateway=self.prefs_gateway,
            on_prefs_changed=on_prefs_changed or (lambda: None),
            prefs_file_path=self.prefs_file_path,
        )

    def create_scheduler(self, tick_callback: Callable[[], None], initial_interval: int = 1) -> RepeatingScheduler:
        """Create scheduler with tick callback."""
        return RepeatingScheduler(initial_interval, tick_callback)

    def rebuild_dependencies(self) -> None:
        """Rebuild dependencies that may be affected by preference changes."""
        # Clear cached instances that depend on preferences
        self._location_service = None
        self._use_case = None
        # Note: We keep presenter and prefs_gateway as they maintain state
