import datetime
import uuid
from enum import StrEnum, auto

from sqlalchemy import JSON
from sqlmodel import SQLModel, Field

from config import Config


class Temporal(StrEnum):
    day = auto()
    bday = auto()
    week = auto()


class Schedule(SQLModel):
    each: int
    temporal: Temporal


class Shift(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    firefighter: str
    start_date: datetime.datetime
    end_date: datetime.datetime


class Rotation(SQLModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    schedule: Schedule = Field(sa_type=JSON)
    fighters: list[str] = Field(sa_type=JSON)
    start_date: datetime.datetime
    # set default end_date as (start_date + 365 days)
    # SQLModel types are not adjusted to recent pydantic changes: https://github.com/fastapi/sqlmodel/discussions/1312
    end_date: datetime.datetime = Field(
        default_factory=lambda data: data["start_date"] + datetime.timedelta(days=365)  # type:ignore[misc,arg-type]
    )
    timezone: str = Field(default_factory=lambda: Config().timezone)

    def __hash__(self) -> int:
        try:
            return uuid.UUID(self.id).int
        except ValueError:
            return hash(self.id)


class RotationORM(Rotation, table=True):
    """
    SQLModel interfere with pydantinc+sqlalchemy init/validation a lot.
    This ends up skipping some pydantic validators and default factories.
    Use inheritance to run pydantic flow first, and proceed with Table Model (sqlalchemy) validations afterward.

    https://github.com/fastapi/sqlmodel/discussions/1312
    https://github.com/fastapi/sqlmodel/issues/134#issuecomment-978409569
    https://sqlmodel.tiangolo.com/tutorial/fastapi/multiple-models/#the-herocreate-data-model
    """

    pass
