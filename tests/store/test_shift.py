from collections.abc import Generator
from datetime import datetime

import pytest
from _pytest.fixtures import FixtureRequest

from models import Rotation, Schedule, Shift, Temporal
from store.shift import ShiftStore
from store.shift_mem import InMemoryShiftStore
from store.shift_sql import SQLAlchemyShiftStore
from tests.conftest import engine


class SQLAlchemyShiftStoreTest(SQLAlchemyShiftStore):  # type: ignore[misc]
    def __init__(self, rotation: Rotation) -> None:
        super().__init__(rotation, engine)


@pytest.fixture()
def rotation() -> Rotation:
    return Rotation(
        id="id0",
        schedule=Schedule(each=2, temporal=Temporal.week),
        fighters=["f1", "f2", "f3"],
        start_date=datetime(2024, 12, 30),
    )


@pytest.fixture()
def shifts() -> list[Shift]:
    return [
        Shift(
            id="id0",
            firefighter="usr_1",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 3),
        ),
        Shift(
            id="id1",
            firefighter="usr_2",
            start_date=datetime(2025, 1, 3),
            end_date=datetime(2025, 1, 5),
        ),
        Shift(
            id="id2",
            firefighter="usr_3",
            start_date=datetime(2025, 1, 5),
            end_date=datetime(2025, 1, 7),
        ),
        # cyclic
        Shift(
            id="id00",
            firefighter="usr_1",
            start_date=datetime(2025, 1, 7),
            end_date=datetime(2025, 3, 9),
        ),
    ]


@pytest.fixture(
    scope="function",
    params=[InMemoryShiftStore, SQLAlchemyShiftStoreTest],
    ids=["mem", "sql"],
)
def store(
    request: FixtureRequest,
    clear_sqlmodel: Generator[None, None, None],
    rotation: Rotation,
) -> ShiftStore:
    # create new instance for each test
    return request.param(rotation)


@pytest.mark.parametrize(
    ["dt", "expected_id"],
    [
        (datetime(2025, 1, 1), "id0"),
        (datetime(2025, 1, 2), "id0"),
        (datetime(2025, 1, 3), "id1"),
        (datetime(2025, 1, 4), "id1"),
        (datetime(2025, 1, 5), "id2"),
        (datetime(2025, 1, 6), "id2"),
        (datetime(2025, 1, 7), "id00"),
        (datetime(2025, 1, 8), "id00"),
    ],
)
def test_shift__find(
    store: ShiftStore,
    dt: datetime,
    expected_id: str,
    rotation: Rotation,
    shifts: list[Shift],
) -> None:
    for s in shifts:
        store.create(s)

    actual_shift = store.find(dt)
    assert actual_shift
    assert actual_shift.id == expected_id


def test_shift__find__should_return_none_if_no_shift_exists(
    store: ShiftStore, rotation: Rotation, shifts: list[Shift]
) -> None:
    assert store.find(datetime(2024, 1, 12)) is None


@pytest.mark.parametrize(
    "dt",
    [
        datetime(1999, 1, 12),
        datetime(2026, 1, 12),
    ],
    ids=[
        "too-far-past",
        "too-far-future",
    ],
)
def test_shift__find__should_return_none_if_no_shifts_meet_conditions(
    store: ShiftStore, dt: datetime, rotation: Rotation, shifts: list[Shift]
) -> None:
    for s in shifts:
        store.create(s)

    assert store.find(dt) is None


def test_shift__list__should_return_all_shifts(
    store: ShiftStore, rotation: Rotation, shifts: list[Shift]
) -> None:
    for s in shifts:
        store.create(s)

    assert store.list() == shifts


@pytest.mark.parametrize(
    "now",
    [
        datetime(2025, 1, 3),
        datetime(2025, 1, 4),
    ],
    ids=[
        "same-as-start-dt",
        "mid-shift",
    ],
)
def test_shift__list__should_return_shifts_by_date(
    store: ShiftStore, now: datetime, rotation: Rotation, shifts: list[Shift]
) -> None:
    for s in shifts:
        store.create(s)

    assert store.list(now) == [
        Shift(
            id="id2",
            firefighter="usr_3",
            start_date=datetime(2025, 1, 5),
            end_date=datetime(2025, 1, 7),
        ),
        Shift(
            id="id00",
            firefighter="usr_1",
            start_date=datetime(2025, 1, 7),
            end_date=datetime(2025, 3, 9),
        ),
    ]


def test_shift__list__should_limit_shifts(
    store: ShiftStore, rotation: Rotation, shifts: list[Shift]
) -> None:
    for s in shifts:
        store.create(s)

    assert store.list(limit=2) == [
        Shift(
            id="id0",
            firefighter="usr_1",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 3),
        ),
        Shift(
            id="id1",
            firefighter="usr_2",
            start_date=datetime(2025, 1, 3),
            end_date=datetime(2025, 1, 5),
        ),
    ]


def test_shift__list__should_return_shifts_by_date_with_limit(
    store: ShiftStore, rotation: Rotation, shifts: list[Shift]
) -> None:
    for s in shifts:
        store.create(s)

    assert store.list(datetime(2025, 1, 4), limit=1) == [
        Shift(
            id="id2",
            firefighter="usr_3",
            start_date=datetime(2025, 1, 5),
            end_date=datetime(2025, 1, 7),
        ),
    ]
