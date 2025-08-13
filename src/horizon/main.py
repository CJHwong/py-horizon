"""Clean composition root using dependency injection."""

from horizon.app_orchestrator import SkyAppOrchestrator
from horizon.container import AppContainer


def run_once() -> None:
    """Execute sky computation once and print the result."""
    container = AppContainer()
    orchestrator = SkyAppOrchestrator(container)
    orchestrator.run_once()


def run_loop() -> None:  # pragma: no cover (integration path)
    """Run the interactive menu bar application with dynamic scheduling."""
    container = AppContainer()
    orchestrator = SkyAppOrchestrator(container)
    orchestrator.run_interactive()


if __name__ == '__main__':  # pragma: no cover
    run_loop()
