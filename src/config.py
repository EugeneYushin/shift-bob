from enum import StrEnum, auto

from pydantic import BaseModel


class Impl(StrEnum):
    mem = auto()


class Config(BaseModel):
    impl: Impl = Impl.mem
    timezone: str = "America/New_York"
