import pytest

from soundtrack_analyzer.utils import (
    extract_timestamp,
    format_delta,
    to_datetime,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("20230705_075056_tp00084.mp4", "2023-07-05 07:50:56"),
        ("20231012_182732_tp00111.mp4", "2023-10-12 18:27:32"),
        ("20231215_093653_tp00033.mp4", "2023-12-15 09:36:53"),
    ],
)
def test_timestamp_extraction(value, expected):
    assert str(extract_timestamp(value)) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (53.0, "2000-01-01 00:00:53"),
        (75.2, "2000-01-01 00:01:15.200000"),
        (5_630.0, "2000-01-01 01:33:50"),
    ],
)
def test_sec2datetime_conversion(value, expected):
    assert str(to_datetime(value)) == expected


@pytest.mark.parametrize(
    "value",
    (3.21, 3.91, 3.00),
)
def test_delta_formatter(value):
    delta = format_delta(value)

    assert delta == "0:00:03"
