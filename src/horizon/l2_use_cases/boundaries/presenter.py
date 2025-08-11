"""Presenter boundary."""

from typing import Protocol

from horizon.l1_entities.models import SkySnapshot


class ISkyPresenter(Protocol):
    def present(self, snapshot: SkySnapshot) -> None:  # side-effect (update view model / UI adapter)
        ...
