
import pytest

from salon_booking import arrival_status, can_book, extra_time_charge


@pytest.mark.parametrize(
    ("service", "duration", "stylist", "member", "expected"),
    [
        ("haircut", 30, "junior", False, 0),
        ("haircut", 31, "junior", False, 10),
        ("haircut", 45, "junior", True, 0),
        ("spa", 91, "junior", True, 10),
        ("haircut", 91, "junior", False, 61 * 18),
        ("haircut", 91, "senior", False, 61 * 30),
    ],
)
def test_extra_time_charge_branches(
    service, duration, stylist, member, expected
):
    assert extra_time_charge(
        service, duration, stylist, member
    ) == expected


@pytest.mark.parametrize(
    ("service", "duration", "message"),
    [
        ("nails", 30, "unknown service"),
        ("haircut", -1, "invalid duration"),
    ],
)
def test_extra_time_charge_rejects_invalid_input(
    service, duration, message
):
    with pytest.raises(ValueError, match=message):
        extra_time_charge(service, duration, "junior", False)


@pytest.mark.parametrize(
    ("party_size", "services", "walk_in", "expected"),
    [
        (2, 1, True, True),
        (3, 1, True, False),
        (5, 1, False, False),
        (4, 2, False, True),
        (4, 3, False, False),
    ],
)
def test_can_book_branches(party_size, services, walk_in, expected):
    assert can_book(party_size, services, walk_in) is expected


@pytest.mark.parametrize(
    ("minutes_early", "is_colour", "is_weekend", "expected"),
    [
        (5, False, False, "open"),
        (4, False, False, "late"),
        (-11, False, False, "closed"),
        (10, True, False, "open"),
        (9, True, False, "late"),
        (20, True, True, "open"),
        (5, True, True, "late"),
        (4, True, True, "closed"),
    ],
)
def test_arrival_status_branches(
    minutes_early, is_colour, is_weekend, expected
):
    assert arrival_status(
        minutes_early, is_colour, is_weekend
    ) == expected
