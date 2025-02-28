import functools

from sqlalchemy import Engine
from sqlmodel import create_engine

from config import Config


@functools.cache
def global_engine() -> Engine:
    cfg = Config()
    if sql_cfg := cfg.sql:
        return create_engine(sql_cfg.url, echo=True)
    raise ValueError("SQL section is not set in Config")
