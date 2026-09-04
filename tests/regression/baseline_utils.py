"""Shared definitions for the regression fixture and its committed baseline.

The fixture is a fixed, synthetic measurement with deliberately injected faults.
Both `generate_baseline.py` (which writes the committed artefacts) and
`test_baseline.py` (which asserts against them) import from here, so the fixture
spec exists in exactly one place.

Fixture and baseline both live under `tests/`, because they are owned entirely
by the test suite. DataForge itself has no data directory - the CLI reads
whatever paths it is given.

Every value below is chosen to be exactly representable as a float64, so sample
values and timestamps round-trip through the `.mf4` unchanged and their string
formatting in check messages is stable across platforms.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml
from asammdf import MDF, Signal

_HERE = Path(__file__).resolve().parent

FIXTURE_MDF = _HERE / "fixtures" / "regression_v1.mf4"
FIXTURE_RULES = _HERE / "fixtures" / "regression_v1_rules.yaml"
BASELINE_JSON = _HERE / "baselines" / "regression_v1.json"

# A regular 2 Hz timebase shared by the first channel group.
TIMEBASE = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]

# A second group whose timebase has a deliberate gap between t=1.0 and t=3.0,
# modelling dropped samples. A separate group is required because MDF channels
# can only share a group when they share a timebase.
DROPOUT_TIMEBASE = [0.0, 0.5, 1.0, 3.0, 3.5]

#: Channel group 1 - name -> (samples, unit). Faults are documented per channel.
UNIFORM_CHANNELS: dict[str, tuple[list[float], str]] = {
    # Clean ramp, fully inside its limits. Establishes the passing case.
    "speed": ([0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0], "km/h"),
    # FAULT - out-of-range spike: 9500 rpm at t=2.0, against a 8000 rpm limit.
    # This is the only check expected to fail.
    "engine_rpm": (
        [800.0, 850.0, 900.0, 950.0, 9500.0, 950.0, 900.0, 850.0, 800.0, 800.0],
        "rpm",
    ),
    # FAULT - stale/frozen signal: the value never changes. It stays inside its
    # limits, so the range check passes. The baseline therefore records that a
    # frozen signal is currently NOT detected; when a stale check is added, this
    # baseline must be updated deliberately.
    "coolant_temp": ([90.0] * 10, "degC"),
}

#: Channel group 2 - the dropped-sample channel.
DROPOUT_CHANNELS: dict[str, tuple[list[float], str]] = {
    # FAULT - dropped samples: five samples over a window that should hold nine.
    # Values stay in range, so this documents that a gap in the timebase does
    # not by itself fail any currently implemented check.
    "wheel_speed": ([0.0, 10.0, 20.0, 80.0, 90.0], "km/h"),
}

#: Rules applied to the fixture, in the order their results are reported.
RULES: list[dict] = [
    {
        "type": "range",
        "channel": "speed",
        "parameters": {"min_value": 0, "max_value": 232},
    },
    {
        "type": "range",
        "channel": "engine_rpm",
        "parameters": {"min_value": 0, "max_value": 8000},
    },
    {
        "type": "range",
        "channel": "coolant_temp",
        "parameters": {"min_value": -40, "max_value": 120},
    },
    {
        "type": "range",
        "channel": "wheel_speed",
        "parameters": {"min_value": 0, "max_value": 232},
    },
]


def write_fixture_mdf(path: Path) -> Path:
    """Write the fixed regression measurement file.

    The two channel groups are appended separately so each keeps its own
    timebase - that is what makes the dropped-sample gap representable.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with MDF(version="4.10") as mdf:
        for channels, timebase in (
            (UNIFORM_CHANNELS, TIMEBASE),
            (DROPOUT_CHANNELS, DROPOUT_TIMEBASE),
        ):
            mdf.append(
                [
                    Signal(
                        samples=np.asarray(samples, dtype=np.float64),
                        timestamps=np.asarray(timebase, dtype=np.float64),
                        name=name,
                        unit=unit,
                    )
                    for name, (samples, unit) in channels.items()
                ],
                comment="DataForge regression fixture v1",
            )
        mdf.save(path, overwrite=True)
    return path


def write_fixture_rules(path: Path) -> Path:
    """Write the fixed rules file applied to the regression fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"checks": RULES}, sort_keys=False))
    return path


def normalise_report(payload: dict) -> dict:
    """Strip machine-specific detail so a report can be compared to a baseline.

    `source_file` and `rules_yaml` record whatever path the CLI was given, which
    is absolute and therefore differs per machine and per run directory. Only
    their file names are stable, so the comparison uses those.
    """
    normalised = dict(payload)
    for key in ("source_file", "rules_yaml"):
        if key in normalised:
            normalised[key] = Path(normalised[key]).name
    return normalised
