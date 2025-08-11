"""Scheduler abstraction; for now uses simple threading.Timer loop."""

import threading
from collections.abc import Callable


class RepeatingScheduler:
    def __init__(self, interval_seconds: float, callback: Callable[[], None]) -> None:
        self.interval = interval_seconds
        self.callback = callback
        self._timer: threading.Timer | None = None
        self._stopped = False

    def _run(self) -> None:
        if self._stopped:
            return
        try:
            self.callback()
        finally:
            self._schedule()

    def _schedule(self) -> None:
        self._timer = threading.Timer(self.interval, self._run)
        self._timer.daemon = True
        self._timer.start()

    def start(self) -> None:
        self._schedule()

    def stop(self) -> None:
        self._stopped = True
        if self._timer:
            self._timer.cancel()
