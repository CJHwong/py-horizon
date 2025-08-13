"""Application orchestrator for managing sky computation workflows."""

from horizon.container import AppContainer
from horizon.l1_entities import SkyRegime
from horizon.l3_interface_adapters.presenters.sky_presenter import InMemorySkyPresenter


class SkyAppOrchestrator:
    """Orchestrates the sky computation application workflow."""

    def __init__(self, container: AppContainer):
        self.container = container

    def run_once(self) -> None:
        """Execute sky computation once and print result."""
        # Execute the use case
        self.container.use_case.execute()

        # Get the result and display it
        presenter = self.container.presenter
        if isinstance(presenter, InMemorySkyPresenter) and presenter.latest:
            vm = presenter.latest

            # Create UI for compatibility (but don't actually show it)
            ui = self.container.create_menu_app()
            ui.update(vm)

            print(f'Gradient horizon={vm.horizon_hex} zenith={vm.zenith_hex} regime={vm.regime}')

    def run_interactive(self) -> None:
        """Run the interactive menu bar application."""

        # Create preferences change handler
        def on_prefs_changed() -> None:
            # Rebuild dependencies and re-execute
            self.container.rebuild_dependencies()
            self.container.use_case.execute()

            presenter = self.container.presenter
            if isinstance(presenter, InMemorySkyPresenter) and presenter.latest:
                ui.update(presenter.latest)

        # Create UI
        ui = self.container.create_menu_app(on_prefs_changed)

        # Create scheduler with dynamic interval adjustment
        def tick() -> None:
            self.container.use_case.execute()

            presenter = self.container.presenter
            if isinstance(presenter, InMemorySkyPresenter) and presenter.latest:
                vm = presenter.latest
                ui.update(vm)
                print(f'[{vm.regime}] horizon={vm.horizon_hex} zenith={vm.zenith_hex} avg={vm.avg_hex}')

                # Adjust scheduler interval based on regime
                if vm.regime in {
                    SkyRegime.LOW_SUN.value,
                    SkyRegime.CIVIL.value,
                    SkyRegime.NAUTICAL.value,
                    SkyRegime.ASTRONOMICAL.value,
                }:
                    scheduler.interval = 90  # Faster updates during twilight
                else:
                    scheduler.interval = 900  # Normal updates

        # Start scheduler
        scheduler = self.container.create_scheduler(tick, initial_interval=1)
        scheduler.start()

        # Run UI loop
        try:
            ui.quit_button = None
            ui.run()  # blocking
        finally:
            scheduler.stop()
