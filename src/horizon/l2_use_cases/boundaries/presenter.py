"""Presenter boundary."""

from typing import Protocol

from horizon.l1_entities import SkySnapshot


class SkyPresenter(Protocol):
    def present(self, snapshot: SkySnapshot) -> None:  # side-effect (update view model / UI adapter)
        ...
