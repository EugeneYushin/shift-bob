import datetime as dt


from shifter import BDayShifter


def test_bdayshifter__should_skip_weekends():
    shifter = BDayShifter(start_dt=dt.datetime(2024, 12, 30), end_dt=dt.datetime(2025, 1, 12))
    assert list(shifter.get_index(2)) == [
        dt.datetime(2024, 12, 30),
        dt.datetime(2025, 1, 1),
        dt.datetime(2025, 1, 3),
        dt.datetime(2025, 1, 7),
        dt.datetime(2025, 1, 9),
    ]
