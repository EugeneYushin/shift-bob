import pytest
from datetime import datetime

from models import Rotation, Schedule, Temporal, Shift
from store.shift import InMemoryShiftStore


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
            id="id0",
            firefighter="usr_1",
            start_date=datetime(2025, 1, 7),
            end_date=datetime(2025, 3, 9),
        ),
    ]


# TODO add tests to create a shift starting on weekend


@pytest.mark.parametrize(
    ["dt", "expected_id"],
    [
        (datetime(2025, 1, 1), "id0"),
        (datetime(2025, 1, 2), "id0"),
        (datetime(2025, 1, 3), "id1"),
        (datetime(2025, 1, 4), "id1"),
        (datetime(2025, 1, 5), "id2"),
        (datetime(2025, 1, 6), "id2"),
        (datetime(2025, 1, 7), "id0"),
        (datetime(2025, 1, 8), "id0"),
    ],
)
def test_shift__find(
    dt: datetime, expected_id: str, rotation: Rotation, shifts: list[Shift]
) -> None:
    store = InMemoryShiftStore(rotation)

    for s in shifts:
        store.create(s)

    actual_shift = store.find(dt)
    assert actual_shift
    assert actual_shift.id == expected_id


def test_shift__find__should_return_none_if_no_shift_exists(
    rotation: Rotation, shifts: list[Shift]
) -> None:
    store = InMemoryShiftStore(rotation)
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
    dt: datetime, rotation: Rotation, shifts: list[Shift]
) -> None:
    store = InMemoryShiftStore(rotation)
    for s in shifts:
        store.create(s)

    assert store.find(dt) is None


def test_shift__list__should_return_all_shifts(
    rotation: Rotation, shifts: list[Shift]
) -> None:
    store = InMemoryShiftStore(rotation)
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
    now: datetime, rotation: Rotation, shifts: list[Shift]
) -> None:
    store = InMemoryShiftStore(rotation)
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
            id="id0",
            firefighter="usr_1",
            start_date=datetime(2025, 1, 7),
            end_date=datetime(2025, 3, 9),
        ),
    ]


def test_shift__list__should_limit_shifts(
    rotation: Rotation, shifts: list[Shift]
) -> None:
    store = InMemoryShiftStore(rotation)
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
    rotation: Rotation, shifts: list[Shift]
) -> None:
    store = InMemoryShiftStore(rotation)
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
