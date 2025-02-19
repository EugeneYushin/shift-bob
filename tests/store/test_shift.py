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


@pytest.mark.parametrize(["dt", "expected_id"], [
    (datetime(2025, 1, 1), "id0"),
    (datetime(2025, 1, 2), "id0"),
    (datetime(2025, 1, 3), "id1"),
    (datetime(2025, 1, 4), "id1"),
    (datetime(2025, 1, 5), "id2"),
    (datetime(2025, 1, 6), "id2"),
    (datetime(2025, 1, 7), "id0"),
    (datetime(2025, 1, 8), "id0"),
])
def test_shift__find(dt: datetime, expected_id: str, rotation: Rotation, shifts: list[Shift]):
    store = InMemoryShiftStore(rotation)

    for s in shifts:
        store.create(s)

    assert store.find(dt).id == expected_id


def test_shift__find__should_return_none_if_no_shift_exists(rotation: Rotation, shifts: list[Shift]):
    store = InMemoryShiftStore(rotation)
    assert store.find(datetime(2024, 1, 12)) is None


@pytest.mark.parametrize("dt", [
    datetime(1999, 1, 12),
    datetime(2026, 1, 12),
], ids=[
    "too-far-past",
    "too-far-future",
])
def test_shift__find__should_return_none_if_no_shifts_meet_conditions(dt: datetime, rotation: Rotation,
                                                                      shifts: list[Shift]):
    store = InMemoryShiftStore(rotation)
    for s in shifts:
        store.create(s)

    assert store.find(dt) is None


def test_shift__list__should_return_all_shifts(rotation: Rotation, shifts: list[Shift]):
    store = InMemoryShiftStore(rotation)
    for s in shifts:
        store.create(s)

    assert store.list() == shifts


@pytest.mark.parametrize("now", [
    datetime(2025, 1, 3), datetime(2025, 1, 4),
], ids=[
    "same-as-start-dt",
    "mid-shift",
])
def test_shift__list__should_return_shifts_by_date(now: datetime, rotation: Rotation, shifts: list[Shift]):
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


def test_shift__list__should_limit_shifts(rotation: Rotation, shifts: list[Shift]):
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


def test_shift__list__should_return_shifts_by_date_with_limit(rotation: Rotation, shifts: list[Shift]):
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

# def test_shift_daily__should_create_shifts():
#     rotation = Rotation(
#         schedule=Schedule(each=1, temporal=Temporal.day),
#         fighters=["usr1", "usr2", "usr3"],
#         start_date=datetime.datetime(2024, 12, 30),
#     )
#
#     store = InMemoryShiftStore(rotation)
#     shift = store.get_or_create(datetime.datetime(2024, 1, 1))
#
#     assert shift == Shift(
#         id=shift.id,  # set this artificially to actually remove this from equation
#         firefighter="usr3",
#         start_date=datetime.datetime(2025, 1, 1),
#         end_date=datetime.datetime(2025, 1, 2),
#     )
#
#
# def test_shift_daily__should_rotate_shifts_in_cycle():
#     rotation = Rotation(
#         schedule=Schedule(each=1, temporal=Temporal.day),
#         fighters=["usr1", "usr2", "usr3"],
#         start_date=datetime.datetime(2024, 12, 30),
#     )
#
#     store = InMemoryShiftStore(rotation)
#     shift = store.get_or_create(datetime.datetime(2024, 1, 8))
#
#     assert shift == Shift(
#         id=shift.id,  # set this artificially to actually remove this from equation
#         firefighter="usr2",
#         start_date=datetime.datetime(2025, 1, 8),
#         end_date=datetime.datetime(2025, 1, 9),
#     )
#
#
# @pytest.mark.parametrize(
#     ["now", "shift_start", "shift_end", "fighter"],
#     [
#         (datetime.datetime(2024, 1, 1, 10), datetime.datetime(2024, 12, 30, 11), datetime.datetime(2025, 1, 1, 11),
#          "usr1"),
#         (datetime.datetime(2024, 1, 1, 11), datetime.datetime(2025, 1, 1, 11), datetime.datetime(2025, 1, 3, 11),
#          "usr2"),
#     ],
#     ids=["prev-shift", "next-shift"],
# )
# def test_shift_daily__should_respect_hour(now: datetime.datetime, shift_start: datetime.datetime,
#                                           shift_end: datetime.datetime, fighter: str):
#     rotation = Rotation(
#         schedule=Schedule(each=2, temporal=Temporal.day),
#         fighters=["usr1", "usr2", "usr3"],
#         start_date=datetime.datetime(2024, 12, 30, 11),
#     )
#
#     store = InMemoryShiftStore(rotation)
#     shift = store.get_or_create(now)
#
#     assert shift == Shift(
#         id=shift.id,  # set this artificially to actually remove this from equation
#         firefighter=fighter,
#         start_date=shift_start,
#         end_date=shift_end,
#     )
#
#
#
#
# def test_shift_daily__should_end_on_next_business_day_instead_of_weekend():
#     rotation = Rotation(
#         schedule=Schedule(each=2, temporal=Temporal.day),
#         fighters=["usr1", "usr2", "usr3"],
#         start_date=datetime.datetime(2024, 12, 31),
#     )
#
#     store = InMemoryShiftStore(rotation)
#     shift = store.get_or_create(datetime.datetime(2025, 1, 4))
#
#     assert shift == Shift(
#         id=shift.id,  # set this artificially to actually remove this from equation
#         firefighter="usr2",
#         start_date=datetime.datetime(2025, 1, 2),
#         end_date=datetime.datetime(2025, 1, 6),
#     )
#
#
# def test_shift__should_create_weekly_shifts():
#     rotation = Rotation(
#         schedule=Schedule(each=1, temporal=Temporal.week),
#         fighters=["usr1", "usr2", "usr3"],
#         start_date=datetime.datetime(2024, 12, 30),
#     )
#
#     store = InMemoryShiftStore(rotation)
#     shift = store.get_or_create(datetime.datetime(2025, 1, 2))
#
#     assert shift == Shift(
#         id=shift.id,  # set this artificially to actually remove this from equation
#         firefighter="usr1",
#         start_date=datetime.datetime(2024, 1, 30),
#         end_date=datetime.datetime(2024, 1, 6),
#     )
#
#
# @pytest.mark.parametrize(
#     ["now", "rotation"],
#     [
#         (
#             datetime.datetime(2023, 1, 1),
#             Rotation(
#                 schedule=Schedule(each=2, temporal=Temporal.day),
#                 fighters=["usr1", "usr2", "usr3"],
#                 start_date=datetime.datetime(2024, 12, 31),
#             ),
#         ),
#         (
#             datetime.datetime(2025, 1, 11),
#             Rotation(
#                 schedule=Schedule(each=2, temporal=Temporal.day),
#                 fighters=["usr1", "usr2", "usr3"],
#                 start_date=datetime.datetime(2024, 12, 31),
#                 end_date=datetime.datetime(2025, 1, 10),
#             ),
#         ),
#     ],
#     ids=["now-in-past", "now-after-end-date"]
# )
# def test_shift__should_raise_if_rotation_is_not_active(now: datetime.datetime, rotation: Rotation):
#     store = InMemoryShiftStore(rotation)
#     with pytest.raises(BobException):
#         store.get_or_create(now)
