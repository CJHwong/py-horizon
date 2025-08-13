"""Location service boundary."""

from typing import Protocol

from horizon.l1_entities import Location


class LocationGateway(Protocol):
    def current_location(self) -> Location | None: ...
