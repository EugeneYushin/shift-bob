from enum import StrEnum, auto

from pydantic import BaseModel


class Impl(StrEnum):
    mem = auto()


class SlackMode(StrEnum):
    http = auto()
    socket = auto()


class Config(BaseModel):
    mode: SlackMode = SlackMode.socket
    port: int = 3000
    impl: Impl = Impl.mem
    timezone: str = "America/New_York"
