import datetime

from models import Rotation, Shift
from store.shift import ShiftStore


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
