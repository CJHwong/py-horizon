"""Composition root and CLI fallback runner with dynamic scheduling."""

from pathlib import Path

from horizon.l1_entities.regimes import SkyRegime
from horizon.l2_use_cases.compute_sky_use_case import ComputeSkyUseCase
from horizon.l3_interface_adapters.gateways.cached_location_gateway import CachedLocationGateway
from horizon.l3_interface_adapters.gateways.ip_location_gateway import IPLocationGateway
from horizon.l3_interface_adapters.gateways.open_meteo_weather_gateway import OpenMeteoWeatherGateway
from horizon.l3_interface_adapters.gateways.prefs_gateway import JsonPreferencesGateway
from horizon.l3_interface_adapters.presenters.sky_presenter import InMemorySkyPresenter
from horizon.l4_frameworks_and_drivers.menu_app import MenuApp
from horizon.l4_frameworks_and_drivers.scheduler import RepeatingScheduler


def run_once() -> None:
    prefs_path = Path('prefs.json')
    prefs_gateway = JsonPreferencesGateway(prefs_path)
    presenter = InMemorySkyPresenter()
    location_service = CachedLocationGateway(IPLocationGateway(), prefs_gateway)
    weather = OpenMeteoWeatherGateway()
    interactor = ComputeSkyUseCase(presenter, location_service, prefs_gateway, weather=weather)
    interactor.execute()
    vm = presenter.latest
    if vm:
        ui = MenuApp(prefs_gateway=prefs_gateway, on_prefs_changed=lambda: None, prefs_file_path=prefs_path)
        ui.update(vm)
        print(f'Gradient horizon={vm.horizon_hex} zenith={vm.zenith_hex} regime={vm.regime}')


def run_loop() -> None:  # pragma: no cover (integration path)
    prefs_path = Path('prefs.json')
    prefs_gateway = JsonPreferencesGateway(prefs_path)
    presenter = InMemorySkyPresenter()
    location_service = CachedLocationGateway(IPLocationGateway(), prefs_gateway)
    weather = OpenMeteoWeatherGateway()
    interactor = ComputeSkyUseCase(presenter, location_service, prefs_gateway, weather=weather)

    def on_prefs_changed() -> None:  # pragma: no cover - UI thread
        # Reload prefs and rebuild dependent services (weather, location precision etc.)
        nonlocal weather, location_service, interactor
        # Rebuild location service with new preferences
        location_service = CachedLocationGateway(IPLocationGateway(), prefs_gateway)
        interactor = ComputeSkyUseCase(presenter, location_service, prefs_gateway, weather=weather)
        interactor.execute()
        vm2 = presenter.latest
        if vm2:
            ui.update(vm2)

    ui = MenuApp(prefs_gateway=prefs_gateway, on_prefs_changed=on_prefs_changed, prefs_file_path=prefs_path)

    def tick() -> None:
        interactor.execute()
        vm = presenter.latest
        if vm:
            ui.update(vm)
            print(f'[{vm.regime}] horizon={vm.horizon_hex} zenith={vm.zenith_hex} avg={vm.avg_hex}')
            # Adjust cadence if twilight
            if vm.regime in {
                SkyRegime.LOW_SUN.value,
                SkyRegime.CIVIL.value,
                SkyRegime.NAUTICAL.value,
                SkyRegime.ASTRONOMICAL.value,
            }:
                scheduler.interval = 90
            else:
                scheduler.interval = 900

    scheduler = RepeatingScheduler(1, tick)  # first tick quickly then adjust
    scheduler.start()

    # Run the UI loop in main thread
    try:
        ui.quit_button = None
        ui.run()  # blocking
    finally:
        scheduler.stop()


if __name__ == '__main__':  # pragma: no cover
    run_loop()
