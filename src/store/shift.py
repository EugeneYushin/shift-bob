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


class InMemoryShiftStore(ShiftStore):
    def __init__(self, rotation: Rotation):
        super().__init__(rotation)
        self._shifts: list[Shift] = []

    def find(self, dt: datetime.datetime) -> Shift | None:
        xl = filter(lambda shift: shift.start_date <= dt < shift.end_date, self._shifts)
        return next(xl, None)

    def list(
        self, dt_from: datetime.datetime | None = None, limit: int | None = None
    ) -> list[Shift]:
        # dt_from = dt_from or datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
        shifts = self._shifts
        if dt_from:
            shifts = list(
                filter(lambda shift: shift.start_date > dt_from, self._shifts)
            )
        return shifts[:limit]

    def create(self, shift: Shift) -> None:
        self._shifts.append(shift)

    def update(self, shift: Shift, new_shift: Shift) -> None:
        # TODO implement
        pass
