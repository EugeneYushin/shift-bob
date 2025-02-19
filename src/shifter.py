import datetime as dt
from abc import ABC, abstractmethod
from typing import Type, assert_never

import pandas as pd
from pandas import DatetimeIndex
from pandas._libs.tslibs import BaseOffset  # TODO str, Timedelta, datetime.timedelta, or DateOffset
from pydantic import BaseModel

from models import Temporal


class Shifter(BaseModel, ABC):
    start_dt: dt.datetime
    end_dt: dt.datetime

    @abstractmethod
    def get_index(self, freq: int) -> DatetimeIndex:
        ...

    @classmethod
    def apply(cls, start_dt: dt.datetime, end_dt: dt.datetime, temporal: Temporal) -> "Shifter":
        match temporal:
            case Temporal.day:
                return DailyShifter(start_dt=start_dt, end_dt=end_dt)
            case Temporal.bday:
                return BDayShifter(start_dt=start_dt, end_dt=end_dt)
            case Temporal.week:
                return WeeklyShifter(start_dt=start_dt, end_dt=end_dt)
            case _:
                assert_never(temporal)


class BaseShifter(Shifter):
    offset: Type[BaseOffset]

    def get_index(self, freq: int) -> DatetimeIndex:
        return pd.date_range(start=self.start_dt, end=self.end_dt, freq=self.offset(freq)).to_pydatetime()


class DailyShifter(BaseShifter):
    offset: Type[BaseOffset] = pd.offsets.Day


class BDayShifter(BaseShifter):
    offset: Type[BaseOffset] = pd.offsets.BDay


class WeeklyShifter(BaseShifter):
    offset: Type[BaseOffset] = pd.offsets.Week
