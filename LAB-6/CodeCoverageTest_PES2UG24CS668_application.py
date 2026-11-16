
import pytest

from salon_booking import arrival_status, can_book, extra_time_charge


@pytest.mark.parametrize(
    ("service", "duration", "stylist", "member", "expected"),
    [
        ("haircut", 40, "junior", True, 0),
        ("haircut", 46, "junior", True, 10),
        ("spa", 91, "junior", True, 10),
        ("haircut", 106, "other", True, 61 * 26),
        ("haircut", 106, "senior", True, 61 * 30),
    ],
)
def test_extra_time_charge_lines(service, duration, stylist, member, expected):
    assert extra_time_charge(service, duration, stylist, member) == expected


@pytest.mark.parametrize(
    ("service", "duration", "message"),
    [
        ("nails", 30, "unknown service"),
        ("haircut", -1, "invalid duration"),
    ],
)
def test_extra_time_charge_invalid_inputs(service, duration, message):
    with pytest.raises(ValueError, match=message):
        extra_time_charge(service, duration, "junior", True)


@pytest.mark.parametrize(
    ("party_size", "services", "walk_in", "expected"),
    [
        (2, 1, True, True),
        (5, 1, False, False),
        (4, 2, False, True),
        (4, 3, False, False),
    ],
)
def test_can_book_lines(party_size, services, walk_in, expected):
    assert can_book(party_size, services, walk_in) is expected


@pytest.mark.parametrize(
    ("minutes_early", "is_colour", "is_weekend", "expected"),
    [
        (20, False, True, "open"),
        (4, False, False, "late"),
        (-11, False, False, "closed"),
        (10, True, True, "late"),
    ],
)
def test_arrival_status_lines(minutes_early, is_colour, is_weekend, expected):
    assert arrival_status(minutes_early, is_colour, is_weekend) == expected
