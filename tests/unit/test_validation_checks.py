"""Unit tests for `dataforge.validation.checks`."""

import pytest

from dataforge.validation.checks import range_check


@pytest.mark.parametrize(
    ("samples", "min_value", "max_value", "expected"),
    [
        pytest.param([10.0, 20.0, 30.0], 0, 100, True, id="all-within-range"),
        pytest.param([0.0, 50.0, 100.0], 0, 100, True, id="bounds-are-inclusive"),
        pytest.param([50.0], 50, 50, True, id="degenerate-range"),
        pytest.param([10.0, 150.0, 30.0], 0, 100, False, id="above-maximum"),
        pytest.param([10.0, -5.0, 30.0], 0, 100, False, id="below-minimum"),
        pytest.param([101.0], 0, 100, False, id="just-above-maximum"),
        pytest.param([-0.1], 0, 100, False, id="just-below-minimum"),
        pytest.param([-10.0, -5.0], -20, 0, True, id="negative-range"),
        # `all([])` equivalent: a channel with no samples has nothing to violate.
        pytest.param([], 0, 100, True, id="no-samples-passes-vacuously"),
        # NaN fails every comparison, so it reads as out-of-range rather than
        # as a distinct "invalid sample" condition.
        pytest.param(
            [10.0, float("nan"), 30.0], 0, 100, False, id="nan-reads-as-out-of-range"
        ),
    ],
)
def test_range_check_outcome(make_signal_set, samples, min_value, max_value, expected):
    signals = make_signal_set({"speed": samples})

    result = range_check("speed", signals, min_value=min_value, max_value=max_value)

    assert result.passed is expected


@pytest.mark.parametrize(
    "expected_fragment",
    [
        pytest.param("speed", id="names-the-channel"),
        pytest.param("150.0", id="names-the-offending-value"),
        pytest.param("0.5", id="names-the-timestamp"),
        pytest.param("outside the specified range", id="explains-the-failure"),
    ],
)
def test_failure_message_is_actionable(make_signal_set, expected_fragment):
    signals = make_signal_set(
        {"speed": [10.0, 150.0, 30.0]}, timestamps=[0.0, 0.5, 1.0]
    )

    result = range_check("speed", signals, min_value=0, max_value=100)

    assert expected_fragment in result.message


def test_reports_the_first_offending_sample(make_signal_set):
    signals = make_signal_set(
        {"speed": [10.0, 150.0, 200.0]}, timestamps=[0.0, 1.0, 2.0]
    )

    result = range_check("speed", signals, min_value=0, max_value=100)

    assert "150.0" in result.message
    assert "200.0" not in result.message


def test_passing_message_names_the_channel(make_signal_set):
    signals = make_signal_set({"speed": [10.0]})

    result = range_check("speed", signals, min_value=0, max_value=100)

    assert "speed" in result.message


@pytest.mark.parametrize(
    ("attribute", "expected"),
    [
        pytest.param("check_name", "range", id="check-name"),
        pytest.param("signal_name", "speed", id="signal-name"),
        pytest.param("parameters", {"min_value": 0, "max_value": 100}, id="parameters"),
    ],
)
def test_result_carries_check_metadata(make_signal_set, attribute, expected):
    signals = make_signal_set({"speed": [10.0]})

    result = range_check("speed", signals, min_value=0, max_value=100)

    assert getattr(result, attribute) == expected


def test_unknown_channel_raises_key_error(make_signal_set):
    signals = make_signal_set({"speed": [10.0]})

    with pytest.raises(KeyError, match="Signal 'rpm' not found"):
        range_check("rpm", signals, min_value=0, max_value=100)
