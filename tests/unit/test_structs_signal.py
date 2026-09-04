"""Unit tests for `dataforge.structs.signal`."""

from pathlib import Path

import numpy as np
import pytest

from dataforge.structs.signal import MeasurementSignal, SignalSet


def test_get_returns_matching_signal(make_signal_set):
    signal_set = make_signal_set({"speed": [1.0, 2.0, 3.0]})

    signal = signal_set.get("speed")

    assert signal.name == "speed"
    np.testing.assert_array_equal(signal.samples, np.array([1.0, 2.0, 3.0]))


@pytest.mark.parametrize(
    ("channels", "lookup"),
    [
        pytest.param({"speed": [1.0]}, "rpm", id="absent-name"),
        pytest.param({"speed": [1.0]}, "Speed", id="wrong-case"),
        pytest.param({}, "speed", id="empty-signal-set"),
    ],
)
def test_get_unknown_signal_raises_key_error(make_signal_set, channels, lookup):
    signal_set = make_signal_set(channels)

    with pytest.raises(KeyError, match="not found in the provided SignalSet"):
        signal_set.get(lookup)


def test_signal_set_retains_source_path(make_signal_set):
    signal_set = make_signal_set({"speed": [1.0]}, source=Path("/tmp/example.mf4"))

    assert signal_set.source == Path("/tmp/example.mf4")


@pytest.mark.parametrize(
    "unit",
    [
        pytest.param("km/h", id="with-unit"),
        pytest.param(None, id="without-unit"),
    ],
)
def test_measurement_signal_accepts_optional_unit(unit):
    signal = MeasurementSignal(
        name="speed",
        samples=np.array([1.0, 2.0]),
        timestamps=np.array([0.0, 0.1]),
        unit=unit,
    )

    assert signal.unit == unit


def test_measurement_signal_stores_parallel_arrays():
    signal = MeasurementSignal(
        name="speed",
        samples=np.array([1.0, 2.0]),
        timestamps=np.array([0.0, 0.1]),
        unit="km/h",
    )

    assert len(signal.samples) == len(signal.timestamps)


def test_signal_set_may_be_empty():
    assert SignalSet(signals={}, source=Path("empty.mf4")).signals == {}
