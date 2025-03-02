import functools
import json
from typing import Any

from pydantic_core import to_jsonable_python
from sqlalchemy import Engine, StaticPool
from sqlmodel import create_engine, SQLModel

from config import Config


def json_serializer(obj: Any) -> str:
    """
    Encodes json in the same way that pydantic does.
    https://github.com/pydantic/pydantic/discussions/6652#discussioncomment-9973045
    """
    return json.dumps(to_jsonable_python(obj))


@functools.cache
def global_engine() -> Engine:
    cfg = Config()
    if sql_cfg := cfg.sql:
        # https://docs.sqlalchemy.org/en/13/dialects/sqlite.html#threading-pooling-behavior
        # multithreading access to SQLLite memory connections
        connect_args = {"check_same_thread": False}
        engine = create_engine(
            sql_cfg.url,
            json_serializer=json_serializer,
            echo=True,
            connect_args=connect_args,
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(engine)
        return engine
    raise ValueError("SQL section is not set in Config")
