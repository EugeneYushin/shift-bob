import datetime as dt
from zoneinfo import ZoneInfo

import pytest

from models import Rotation, Schedule, Shift, Temporal
from service.oncall import OncallService
from store.factory import InMemoryStoreFactory, SQLStoreFactory
from tests.conftest import engine


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


def test_oncall_service__create_rotation_with_timezone() -> None:
    svc = OncallService(InMemoryStoreFactory())

    rotation = Rotation(
        schedule=Schedule(each=1, temporal=Temporal.day),
        fighters=["f1", "f2", "f3"],
        start_date=dt.datetime(2025, 1, 1, 9),
        end_date=dt.datetime(2025, 1, 4, 9),
        timezone="America/New_York",
    )

    shifts = svc.create_rotation(rotation)
    assert len(shifts) == 3
    # EST = UTC−05:00
    assert shifts == [
        Shift(
            id=shifts[0].id,
            firefighter="f1",
            start_date=dt.datetime(2025, 1, 1, 14, tzinfo=dt.timezone.utc),
            end_date=dt.datetime(2025, 1, 2, 14, tzinfo=dt.timezone.utc),
        ),
        Shift(
            id=shifts[1].id,
            firefighter="f2",
            start_date=dt.datetime(2025, 1, 2, 14, tzinfo=dt.timezone.utc),
            end_date=dt.datetime(2025, 1, 3, 14, tzinfo=dt.timezone.utc),
        ),
        Shift(
            id=shifts[2].id,
            firefighter="f3",
            start_date=dt.datetime(2025, 1, 3, 14, tzinfo=dt.timezone.utc),
            end_date=dt.datetime(2025, 1, 4, 14, tzinfo=dt.timezone.utc),
        ),
    ]


def test_oncall_service__create_rotation_with_timezone_over_dst() -> None:
    svc = OncallService(InMemoryStoreFactory())

    rotation = Rotation(
        schedule=Schedule(each=2, temporal=Temporal.day),
        fighters=["f1", "f2", "f3"],
        # dates cross DST
        start_date=dt.datetime(2025, 3, 8, 9),
        end_date=dt.datetime(2025, 3, 12, 9),
        timezone="America/New_York",
    )

    shifts = svc.create_rotation(rotation)
    assert len(shifts) == 2
    # EST = UTC−05:00
    assert shifts == [
        Shift(
            id=shifts[0].id,
            firefighter="f1",
            start_date=dt.datetime(2025, 3, 8, 14, tzinfo=dt.timezone.utc),
            # UTC is shifted from 14 to 13 with respect to EST->EDT shift
            end_date=dt.datetime(2025, 3, 10, 13, tzinfo=dt.timezone.utc),
        ),
        Shift(
            id=shifts[1].id,
            firefighter="f2",
            start_date=dt.datetime(2025, 3, 10, 13, tzinfo=dt.timezone.utc),
            end_date=dt.datetime(2025, 3, 12, 13, tzinfo=dt.timezone.utc),
        ),
    ]


def test_oncall_service__get_current_shift(rotation: Rotation) -> None:
    svc = OncallService(InMemoryStoreFactory())
    svc.create_rotation(rotation)

    actual_shift = svc.get_current_shift(
        dt.datetime(2024, 12, 31, tzinfo=dt.timezone.utc)
    )
    assert actual_shift
    assert actual_shift == Shift(
        id=actual_shift.id,
        firefighter="f1",
        start_date=dt.datetime(2024, 12, 30, tzinfo=dt.timezone.utc),
        end_date=dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc),
    )


def test_oncall_service__get_current_shift_with_timezone() -> None:
    utc_dt = dt.datetime(2025, 1, 2, tzinfo=dt.timezone.utc)  # 2025, 1, 2, 0, 0
    etc_dt = utc_dt.astimezone(tz=ZoneInfo("America/New_York"))  # 2025, 1, 1, 19, 0

    rotation = Rotation(
        schedule=Schedule(each=1, temporal=Temporal.bday),
        fighters=["f1", "f2", "f3"],
        start_date=dt.datetime(2025, 1, 1),
        end_date=dt.datetime(2025, 1, 3),
        timezone="UTC",
    )

    svc = OncallService(SQLStoreFactory(engine))
    svc.create_rotation(rotation)

    utc_shift = svc.get_current_shift(utc_dt)
    assert utc_shift
    assert utc_shift == Shift(
        id=utc_shift.id,
        firefighter="f2",
        start_date=dt.datetime(2025, 1, 2),
        end_date=dt.datetime(2025, 1, 3),
    )

    assert utc_shift == svc.get_current_shift(etc_dt)


def test_oncall_service__get_current_shift_returns_none_if_rotation_not_exists() -> (
    None
):
    svc = OncallService(InMemoryStoreFactory())
    assert svc.get_current_shift() is None


@pytest.mark.parametrize(
    "now",
    [
        dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2099, 1, 1, tzinfo=dt.timezone.utc),
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
    [
        dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2025, 1, 2, tzinfo=dt.timezone.utc),
    ],
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
            start_date=dt.datetime(2025, 1, 1, 0, tzinfo=dt.timezone.utc),
            end_date=dt.datetime(2025, 1, 3, 0, tzinfo=dt.timezone.utc),
        ),
        Shift(
            id=shifts[2].id,
            firefighter="f3",
            start_date=dt.datetime(2025, 1, 3, 0, tzinfo=dt.timezone.utc),
            end_date=dt.datetime(2025, 1, 7, 0, tzinfo=dt.timezone.utc),
        ),
        Shift(
            id=shifts[3].id,
            firefighter="f1",
            start_date=dt.datetime(2025, 1, 7, 0, tzinfo=dt.timezone.utc),
            end_date=dt.datetime(2025, 1, 9, 0, tzinfo=dt.timezone.utc),
        ),
    ]


def test_oncall_service__get_shifts_returns_empty_list_if_rotation_not_exists() -> None:
    svc = OncallService(InMemoryStoreFactory())
    assert svc.get_shifts(dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)) == []


@pytest.mark.parametrize(
    "now",
    [
        dt.datetime(1990, 1, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc),
    ],
    ids=["past", "future"],
)
def test_oncall_service__get_shifts_returns_empty_list_if_shift_not_exists(
    now: dt.datetime, rotation: Rotation
) -> None:
    svc = OncallService(InMemoryStoreFactory())
    svc.create_rotation(rotation)

    assert svc.get_shifts(now) == []
