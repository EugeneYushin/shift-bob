import datetime as dt

import pytest

from models import Rotation, Schedule, Shift, Temporal
from service.oncall import OncallService
from store.factory import InMemoryStoreFactory


@pytest.fixture()
def rotation() -> Rotation:
    return Rotation(
        id="id0",
        schedule=Schedule(each=2, temporal=Temporal.bday),
        fighters=["f1", "f2", "f3"],
        start_date=dt.datetime(2024, 12, 30),
        end_date=dt.datetime(2025, 1, 31),
    )


def test_oncall_service__create_rotation(rotation: Rotation) -> None:
    svc = OncallService(InMemoryStoreFactory())
    shifts = svc.create_rotation(rotation)
    assert len(shifts) == 12


def test_oncall_service__get_current_shift(rotation: Rotation) -> None:
    svc = OncallService(InMemoryStoreFactory())
    svc.create_rotation(rotation)

    actual_shift = svc.get_current_shift(dt.datetime(2024, 12, 31))
    assert actual_shift
    assert actual_shift == Shift(
        id=actual_shift.id,
        firefighter="f1",
        start_date=dt.datetime(2024, 12, 30),
        end_date=dt.datetime(2025, 1, 1),
    )


def test_oncall_service__get_current_shift_returns_none_if_rotation_not_exists() -> (
    None
):
    svc = OncallService(InMemoryStoreFactory())
    assert svc.get_current_shift() is None


@pytest.mark.parametrize(
    "now",
    [
        dt.datetime(1970, 1, 1),
        dt.datetime(2099, 1, 1),
    ],
    ids=[
        "now-in-past",
        "now-in-future",
    ],
)
def test_oncall_service__get_current_shift_returns_none_if_shift_not_exists(
    now: dt.datetime, rotation: Rotation
) -> None:
    svc = OncallService(InMemoryStoreFactory())
    svc.create_rotation(rotation)

    assert svc.get_current_shift(now) is None


@pytest.mark.parametrize(
    "now",
    [dt.datetime(2025, 1, 1), dt.datetime(2025, 1, 2)],
    ids=["start-shift", "mid-shift"],
)
def test_oncall_service__get_shifts(now: dt.datetime, rotation: Rotation) -> None:
    svc = OncallService(InMemoryStoreFactory())
    shifts = svc.create_rotation(rotation)

    actual_shifts = svc.get_shifts(now, limit=3)
    assert actual_shifts == [
        Shift(
            id=shifts[1].id,
            firefighter="f2",
            start_date=dt.datetime(2025, 1, 1, 0, 0),
            end_date=dt.datetime(2025, 1, 3, 0, 0),
        ),
        Shift(
            id=shifts[2].id,
            firefighter="f3",
            start_date=dt.datetime(2025, 1, 3, 0, 0),
            end_date=dt.datetime(2025, 1, 7, 0, 0),
        ),
        Shift(
            id=shifts[3].id,
            firefighter="f1",
            start_date=dt.datetime(2025, 1, 7, 0, 0),
            end_date=dt.datetime(2025, 1, 9, 0, 0),
        ),
    ]


def test_oncall_service__get_shifts_returns_empty_list_if_rotation_not_exists() -> None:
    svc = OncallService(InMemoryStoreFactory())
    assert svc.get_shifts(dt.datetime(2025, 1, 1)) == []


@pytest.mark.parametrize(
    "now", [dt.datetime(1990, 1, 1), dt.datetime(2026, 1, 1)], ids=["past", "future"]
)
def test_oncall_service__get_shifts_returns_empty_list_if_shift_not_exists(
    now: dt.datetime, rotation: Rotation
) -> None:
    svc = OncallService(InMemoryStoreFactory())
    svc.create_rotation(rotation)

    assert svc.get_shifts(now) == []
