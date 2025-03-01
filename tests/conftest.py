from collections.abc import Generator

import pytest
from sqlmodel import create_engine, SQLModel

from store.sa import json_serializer

engine = create_engine("sqlite:///:memory:", json_serializer=json_serializer, echo=True)


@pytest.fixture(scope="function")
def clear_sqlmodel() -> Generator[None, None, None]:
    # we might need to import db models first, eg:
    # from models import RotationORM, ShiftORM
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)
