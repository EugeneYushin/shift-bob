import abc
import datetime
import logging
from abc import abstractmethod

from models import Rotation, Shift

logger = logging.getLogger(__name__)


class ShiftStore(abc.ABC):
    def __init__(self, rotation: Rotation):
        self.rotation = rotation

    @abstractmethod
    def find(self, dt: datetime.datetime) -> Shift | None: ...

    @abstractmethod
    def list(
        self, dt_from: datetime.datetime | None = None, limit: int | None = None
    ) -> list[Shift]: ...

    @abstractmethod
    def create(self, shift: Shift) -> None: ...

    @abstractmethod
    # TODO check/remove if not used
    def update(self, shift: Shift, new_shift: Shift) -> None: ...
