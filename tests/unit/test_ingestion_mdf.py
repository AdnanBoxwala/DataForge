"""Unit tests for `dataforge.ingestion.mdf`."""

import logging
from pathlib import Path

import numpy as np
import pytest

from dataforge.ingestion.mdf import MDFIngestor

DUPLICATE_GROUPS = [
    ("speed", [1.0, 2.0], [0.0, 1.0]),
    ("speed", [3.0, 4.0], [0.0, 0.5]),
]


def test_declares_the_mf4_extension():
    assert MDFIngestor.file_extension == ".mf4"


@pytest.mark.parametrize(
    "channels",
    [
        pytest.param({"speed": [1.0, 2.0, 3.0]}, id="single-channel"),
        pytest.param({"speed": [1.0], "rpm": [10.0]}, id="two-channels"),
        pytest.param({"a": [1.0], "b": [2.0], "c": [3.0]}, id="three-channels"),
    ],
)
def test_load_returns_every_channel(make_mdf, channels):
    signal_set = MDFIngestor().load(make_mdf(channels))

    assert set(signal_set.signals) == set(channels)


@pytest.mark.parametrize(
    "timestamps",
    [
        pytest.param([0.0, 0.5, 1.0], id="uniform-timebase"),
        # A dropped sample leaves a gap; the irregular spacing must survive.
        pytest.param([0.0, 0.1, 5.0], id="non-uniform-timebase"),
    ],
)
def test_load_preserves_samples_and_timestamps(make_mdf, timestamps):
    path = make_mdf({"speed": [10.0, 20.0, 30.0]}, timestamps=timestamps)

    signal = MDFIngestor().load(path).get("speed")

    np.testing.assert_allclose(signal.samples, [10.0, 20.0, 30.0])
    np.testing.assert_allclose(signal.timestamps, timestamps)


@pytest.mark.parametrize(
    "unit",
    [
        pytest.param("km/h", id="speed-unit"),
        pytest.param("rpm", id="rotational-unit"),
        pytest.param("", id="no-unit"),
    ],
)
def test_load_preserves_unit(make_mdf, unit):
    path = make_mdf({"speed": [1.0]}, unit=unit)

    assert MDFIngestor().load(path).get("speed").unit == unit


def test_load_sets_source_to_the_file_path(make_mdf):
    path = make_mdf({"speed": [1.0]})

    assert MDFIngestor().load(path).source == path


@pytest.mark.parametrize("attribute", ["samples", "timestamps"])
def test_arrays_are_not_downgraded_to_lists(make_mdf, attribute):
    """Ingestion must preserve numpy arrays - checks rely on them."""
    signal = MDFIngestor().load(make_mdf({"speed": [1.0, 2.0]})).get("speed")

    assert isinstance(getattr(signal, attribute), np.ndarray)


def test_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="does not exist"):
        MDFIngestor().load(tmp_path / "absent.mf4")


def test_duplicate_channel_names_warn(make_multi_group_mdf, caplog):
    path = make_multi_group_mdf(DUPLICATE_GROUPS)

    with caplog.at_level(logging.WARNING, logger="dataforge.ingestion.mdf"):
        MDFIngestor().load(path)

    assert "Duplicate channel name 'speed'" in caplog.text


def test_duplicate_channel_names_keep_the_last_group(make_multi_group_mdf):
    """Documents the silent-overwrite behaviour the warning above flags."""
    signal_set = MDFIngestor().load(make_multi_group_mdf(DUPLICATE_GROUPS))

    assert len(signal_set.signals) == 1
    np.testing.assert_allclose(signal_set.get("speed").samples, [3.0, 4.0])


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(b"this is definitely not an MDF file", id="plain-text"),
        pytest.param(b"", id="empty-file"),
        pytest.param(b"\x00\x01\x02\x03", id="binary-garbage"),
    ],
)
def test_unreadable_file_raises(tmp_path: Path, content: bytes):
    """A non-MDF file must not be silently accepted."""
    path = tmp_path / "corrupt.mf4"
    path.write_bytes(content)

    with pytest.raises(Exception):
        MDFIngestor().load(path)
