"""Shared fixtures for the DataForge test suite."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np
import pytest
import yaml
from asammdf import MDF, Signal

from dataforge.ingestion import base as ingestion_base
from dataforge.structs.signal import MeasurementSignal, SignalSet
from dataforge.validation import base as validation_base


@pytest.fixture
def make_mdf(tmp_path: Path) -> Callable[..., Path]:
    """Return a factory that writes a temporary `.mf4` file.

    All channels share a single timebase, so they land in one channel group.
    """

    def _make(
        channels: dict[str, Sequence[float]],
        timestamps: Sequence[float] | None = None,
        unit: str = "km/h",
        filename: str = "measurement.mf4",
    ) -> Path:
        path = tmp_path / filename
        signals = [
            Signal(
                samples=np.asarray(samples, dtype=float),
                timestamps=np.asarray(
                    timestamps if timestamps is not None else range(len(samples)),
                    dtype=float,
                ),
                name=name,
                unit=unit,
            )
            for name, samples in channels.items()
        ]
        with MDF(version="4.10") as mdf:
            mdf.append(signals)
            mdf.save(path, overwrite=True)
        return path

    return _make


@pytest.fixture
def make_multi_group_mdf(tmp_path: Path) -> Callable[..., Path]:
    """Return a factory that writes a `.mf4` with one channel group per append.

    Each group gets its own timebase, which is what allows two channels to share
    a name across groups - the condition `MDFIngestor` warns about.
    """

    def _make(
        groups: Sequence[tuple[str, Sequence[float], Sequence[float]]],
        filename: str = "multi_group.mf4",
    ) -> Path:
        path = tmp_path / filename
        with MDF(version="4.10") as mdf:
            for name, samples, timestamps in groups:
                mdf.append(
                    [
                        Signal(
                            samples=np.asarray(samples, dtype=float),
                            timestamps=np.asarray(timestamps, dtype=float),
                            name=name,
                            unit="km/h",
                        )
                    ]
                )
            mdf.save(path, overwrite=True)
        return path

    return _make


@pytest.fixture
def make_signal_set() -> Callable[..., SignalSet]:
    """Return a factory that builds an in-memory `SignalSet`."""

    def _make(
        channels: dict[str, Sequence[float]],
        timestamps: Sequence[float] | None = None,
        unit: str | None = "km/h",
        source: Path = Path("measurement.mf4"),
    ) -> SignalSet:
        signals = {}
        for name, samples in channels.items():
            values = np.asarray(samples, dtype=float)
            signals[name] = MeasurementSignal(
                name=name,
                samples=values,
                timestamps=np.asarray(
                    timestamps if timestamps is not None else range(len(values)),
                    dtype=float,
                ),
                unit=unit,
            )
        return SignalSet(signals=signals, source=source)

    return _make


@pytest.fixture
def make_rules_yaml(tmp_path: Path) -> Callable[..., Path]:
    """Return a factory that writes a temporary rules YAML file."""

    def _make(checks: list[dict], filename: str = "rules.yaml") -> Path:
        path = tmp_path / filename
        path.write_text(yaml.safe_dump({"checks": checks}))
        return path

    return _make


@pytest.fixture
def range_rule() -> Callable[..., dict]:
    """Return a factory for a single `range` rule entry."""

    def _make(
        channel: str = "speed", min_value: float = 0, max_value: float = 100
    ) -> dict:
        return {
            "type": "range",
            "channel": channel,
            "parameters": {"min_value": min_value, "max_value": max_value},
        }

    return _make


@pytest.fixture
def isolated_registries():
    """Snapshot and restore the global ingestor/check registries.

    Tests that register their own ingestors or checks would otherwise leak
    entries into every subsequent test in the session.
    """
    ingestors = dict(ingestion_base._INGESTOR_REGISTRY)
    checks = dict(validation_base._CHECK_REGISTRY)
    yield
    ingestion_base._INGESTOR_REGISTRY.clear()
    ingestion_base._INGESTOR_REGISTRY.update(ingestors)
    validation_base._CHECK_REGISTRY.clear()
    validation_base._CHECK_REGISTRY.update(checks)


@pytest.fixture
def restore_root_logger():
    """Restore the root logger after a test reconfigures it.

    `configure_logging` calls `basicConfig(force=True)`, which detaches every
    existing root handler - including the one pytest uses for `caplog`.
    """
    root = logging.getLogger()
    handlers = root.handlers[:]
    level = root.level
    yield
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    for handler in handlers:
        root.addHandler(handler)
    root.setLevel(level)
