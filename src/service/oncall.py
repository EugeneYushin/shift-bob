import datetime
import logging
from itertools import cycle, pairwise
from zoneinfo import ZoneInfo

import pytz

from datetime import UTC
from config import Config
from models import Rotation, Shift
from shifter import Shifter
from store.factory import StoreFactory

logger = logging.getLogger(__name__)


class OncallService:
    def __init__(self, store_factory: StoreFactory):
        self.store_factory = store_factory

    def create_rotation(self, rotation: Rotation) -> list[Shift]:
        """
        Create rotation with all shifts between start and end dates (1 year by default).
        All dates are converted from user specific timezone and stored in UTC.
        """
        logger.debug(f"create {rotation=}")
        rotation = rotation.model_copy()
        tz = pytz.timezone(rotation.timezone)

        # UTC doesn't respect daylight-saving (DST)
        #   Sat, 2025-03-08 09:00 EST -> Sat, 2025-03-08 14:00 UTC
        #   Mon, 2025-03-10 10:00 EDT -> Mon, 2025-03-10 14:00 UTC
        # hence, generate dates with naive datetime first to skip DST offsets
        shifter = Shifter.apply(
            start_dt=rotation.start_date,
            end_dt=rotation.end_date,
            temporal=rotation.schedule.temporal,
        )

        # set timezone with localize, it doesn't change date/time parts (just adds tz info)
        # and then convert to UTC, ie
        # 06:00:00, EST-0500 -> 06:00:00 EST-0500 -> 12:00:00 CET+0100
        rotation.start_date = tz.localize(rotation.start_date).astimezone(UTC)
        rotation.end_date = tz.localize(rotation.end_date).astimezone(UTC)
        self.store_factory.rotation().create(rotation)

        # create all shifts
        fighters = cycle(rotation.fighters)

        shift_store = self.store_factory.shifts(rotation)

        shifts = []
        for start_dt, end_dt in pairwise(shifter.get_index(rotation.schedule.each)):
            shift = Shift(
                firefighter=next(fighters),
                start_date=tz.localize(start_dt).astimezone(UTC),
                end_date=tz.localize(end_dt).astimezone(UTC),
            )
            logger.debug(f"create {shift=}")
            shift_store.create(shift)
            shifts.append(shift)

        return shifts

    def get_current_shift(self, now: datetime.datetime | None = None) -> Shift | None:
        if now is None:
            now = datetime.datetime.now(tz=UTC)

        utc_now = now.astimezone(UTC)
        rotation = self.store_factory.rotation().get_by_date(utc_now)
        if rotation is None:
            return None

        return self.store_factory.shifts(rotation).find(utc_now)

    def get_shifts(
        self, now: datetime.datetime | None = None, limit: int = 5
    ) -> list[Shift]:
        """Sorted list of shifts starting from now."""
        if now is None:
            now = datetime.datetime.now(tz=ZoneInfo(Config().timezone))

        utc_now = now.astimezone(UTC)

        rotation = self.store_factory.rotation().get_by_date(utc_now)
        if rotation is None:
            return []

        shifts_store = self.store_factory.shifts(rotation)
        # TODO should we add current shift to the list or next shifts only?
        current_shift = shifts_store.find(utc_now)
        if current_shift is None:
            return []

        next_shifts = shifts_store.list(utc_now, limit=limit - 1)

        shifts_all = [current_shift, *next_shifts]
        # SQLite doesn't persist timezone (should be passed as timezone formatted str vs datetime object)
        # TODO review if we need to compensate timezone for backends other than SQLite
        return shifts_all
