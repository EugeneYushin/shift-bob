from enum import StrEnum, auto

from pydantic import BaseModel


class Impl(StrEnum):
    mem = auto()
    sql = auto()


class SlackMode(StrEnum):
    http = auto()
    socket = auto()


class SQLConfing(BaseModel):
    url: str


class Config(BaseModel):
    mode: SlackMode = SlackMode.socket
    port: int = 3000
    impl: Impl = Impl.sql
    sql: SQLConfing | None = SQLConfing(url="sqlite:///:memory:")
    timezone: str = "America/New_York"
