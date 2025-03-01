from datetime import datetime
from typing import Generator

import pytest

from models import Rotation, Schedule, Temporal
from store.rotation import InMemoryRotationStore, RotationStore
from store.rotation_sql import SQLAlchemyRotationStore
from tests.conftest import engine


# TODO fix imports from internal API
from _pytest.fixtures import FixtureRequest


# TODO fix typing errors: Class cannot subclass "SQLAlchemyRotationStore" (has type "Any")  [misc]
class SQLAlchemyRotationStoreTest(SQLAlchemyRotationStore):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__(engine)


@pytest.fixture(
    scope="function",
    params=[InMemoryRotationStore, SQLAlchemyRotationStoreTest],
    ids=["mem", "sql"],
)
def store(
    request: FixtureRequest, clear_sqlmodel: Generator[None, None, None]
) -> RotationStore:
    # create new instance for each test
    return request.param()


@pytest.fixture()
def rotations() -> list[Rotation]:
    return [
        # past
        Rotation(
            id="id0",
            schedule=Schedule(each=1, temporal=Temporal.week),
            fighters=["f1", "f2", "f3"],
            start_date=datetime(2024, 1, 1),
        ),
        # current interval
        Rotation(
            id="id1",
            schedule=Schedule(each=1, temporal=Temporal.week),
            fighters=["f1", "f2", "f3"],
            start_date=datetime(2024, 6, 1),
        ),
        # future
        Rotation(
            id="id2",
            schedule=Schedule(each=1, temporal=Temporal.week),
            fighters=["f1", "f2", "f3"],
            start_date=datetime(2025, 3, 1),
        ),
    ]


def test_rotation__get_by_id(store: RotationStore, rotations: list[Rotation]) -> None:
    for r in rotations:
        store.create(r)

    assert store.get_by_id("id0") == rotations[0]


def test_rotation__get_by_id__should_return_none_if_not_exists(
    store: RotationStore,
) -> None:
    assert store.get_by_id("empty") is None


def test_rotation__get_by_date__should_return_closest_rotation(
    store: RotationStore,
    rotations: list[Rotation],
) -> None:
    for r in rotations:
        store.create(r)

    assert store.get_by_date(datetime(2025, 1, 1)) == rotations[1]


def test_rotation__get_by_date__should_return_none_if_not_exists(
    store: RotationStore,
) -> None:
    assert store.get_by_date(datetime(2026, 1, 1)) is None
