"""Location service boundary."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Location:
    lat: float
    lon: float


class LocationGateway(Protocol):
    def current_location(self) -> Location | None: ...
