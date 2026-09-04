"""Unit tests for `dataforge.ingestion.base`."""

from pathlib import Path

import pytest

from dataforge.ingestion.base import (
    _INGESTOR_REGISTRY,
    Ingestor,
    get_ingestor_for,
    register_ingestor,
)
from dataforge.ingestion.mdf import MDFIngestor
from dataforge.structs.signal import SignalSet


class _CSVIngestor(Ingestor):
    """Minimal concrete ingestor used to exercise registration."""

    file_extension = ".csv"

    def load(self, path: Path) -> SignalSet:
        return SignalSet(signals={}, source=path)


def test_mf4_resolves_to_the_mdf_ingestor():
    assert isinstance(get_ingestor_for(Path("measurement.mf4")), MDFIngestor)


def test_mdf_ingestor_is_registered_on_package_import():
    """Regression test: the registry is populated by an import side effect.

    `dataforge.ingestion.__init__` imports `MDFIngestor` purely so the
    `@register_ingestor` decorator runs. That import looks unused, and removing
    it silently empties the registry and breaks every run.
    """
    import dataforge.ingestion  # noqa: F401  (import under test)

    assert ".mf4" in _INGESTOR_REGISTRY


@pytest.mark.parametrize(
    "filename",
    [
        pytest.param("measurement.csv", id="unregistered-extension"),
        pytest.param("measurement.MF4", id="uppercase-extension"),
        pytest.param("measurement", id="no-extension"),
        pytest.param("measurement.mf4.bak", id="wrong-final-extension"),
    ],
)
def test_unresolvable_extension_raises_value_error(filename):
    with pytest.raises(ValueError, match="No ingestor registered for file extension"):
        get_ingestor_for(Path(filename))


@pytest.mark.parametrize(
    "pattern",
    [
        pytest.param("No ingestor registered", id="states-the-problem"),
        pytest.param(r"\.csv", id="names-the-offending-extension"),
        pytest.param(r"\.mf4", id="lists-available-extensions"),
    ],
)
def test_unresolvable_extension_error_is_actionable(pattern):
    with pytest.raises(ValueError, match=pattern):
        get_ingestor_for(Path("measurement.csv"))


def test_register_ingestor_adds_to_registry(isolated_registries):
    register_ingestor(_CSVIngestor)

    assert isinstance(get_ingestor_for(Path("measurement.csv")), _CSVIngestor)


def test_register_ingestor_returns_the_class_unchanged(isolated_registries):
    assert register_ingestor(_CSVIngestor) is _CSVIngestor


def test_get_ingestor_returns_a_new_instance_each_call():
    assert get_ingestor_for(Path("a.mf4")) is not get_ingestor_for(Path("b.mf4"))


def test_ingestor_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        Ingestor()  # type: ignore[abstract]
