import functools
import json
from typing import Any

from pydantic_core import to_jsonable_python
from sqlalchemy import Engine
from sqlmodel import create_engine

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
        return create_engine(sql_cfg.url, json_serializer=json_serializer, echo=True)
    raise ValueError("SQL section is not set in Config")
