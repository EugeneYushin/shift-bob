from enum import StrEnum, auto

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Impl(StrEnum):
    mem = auto()
    sql = auto()


class SlackMode(StrEnum):
    http = auto()
    socket = auto()


class SQLConfing(BaseModel):
    url: str


class Config(BaseSettings):
    mode: SlackMode = SlackMode.socket
    port: int = 3000
    impl: Impl = Impl.sql
    sql: SQLConfing | None = SQLConfing(url="sqlite:///:memory:")
    # timezone: str = "America/New_York"
    timezone: str = "UTC"  # TODO UTC is depicted as "Time zone: Monrovia, Reykjavik" in Slack time-picker

    model_config = SettingsConfigDict(env_prefix="BOB_", env_nested_delimiter="__")
