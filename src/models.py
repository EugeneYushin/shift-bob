import datetime
import uuid
from enum import StrEnum, auto

from pydantic import BaseModel, Field, ConfigDict

from config import Config


class Temporal(StrEnum):
    day = auto()
    bday = auto()
    week = auto()


class Schedule(BaseModel):
    each: int
    temporal: Temporal

    model_config = ConfigDict(frozen=True)


class Shift(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    firefighter: str
    start_date: datetime.datetime
    end_date: datetime.datetime

    model_config = ConfigDict(frozen=True)


class Rotation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    schedule: Schedule
    fighters: list[str]
    start_date: datetime.datetime
    # set default end_date as (start_date + 365 days)
    end_date: datetime.datetime = Field(
        default_factory=lambda data: data["start_date"] + datetime.timedelta(days=365)
    )
    timezone: str = Field(default_factory=lambda _: Config().timezone)

    model_config = ConfigDict(frozen=True)

    def __hash__(self):
        try:
            return uuid.UUID(self.id).int
        except ValueError:
            return hash(self.id)
