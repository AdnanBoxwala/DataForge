"""Regenerate the bundled demo measurement and rules.

    uv run python examples/generate_demo.py

These files exist so that `dataforge` can be run with zero setup - including
from inside the Docker image, which does not ship the test suite. They are a
demonstration, not a test fixture:

  * they are free to change whenever a better illustration comes along, because
    nothing asserts against their exact contents, and
  * every check passes, so a first run exits 0 and shows the happy path.

The frozen fixture that CI asserts against lives in `tests/regression/fixtures/`
and is deliberately the opposite on both counts - never edited, and failing by
design. Do not conflate the two.

Only `demo.mf4` and `demo_rules.yaml` need to be copied into the container; this
script is a development utility.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml
from asammdf import MDF, Signal

HERE = Path(__file__).resolve().parent
DEMO_MDF = HERE / "demo.mf4"
DEMO_RULES = HERE / "demo_rules.yaml"

# A 10-second drive cycle sampled at 2 Hz. Every timestamp is a multiple of 0.5
# so the values round-trip through the .mf4 exactly.
TIMESTAMPS = [i * 0.5 for i in range(20)]

# fmt: off
CHANNELS: dict[str, tuple[list[float], str]] = {
    # Accelerate, cruise, decelerate to a stop.
    "speed": (
        [0.0, 5.0, 12.0, 20.0, 28.0, 35.0, 42.0, 48.0, 52.0, 55.0,
         55.0, 55.0, 54.0, 50.0, 44.0, 36.0, 27.0, 18.0, 9.0, 0.0],
        "km/h",
    ),
    # Engine speed tracking the same profile, settling back to idle.
    "engine_rpm": (
        [800.0, 1200.0, 1600.0, 2000.0, 2200.0, 2400.0, 2500.0, 2400.0, 2300.0, 2200.0,
         2100.0, 2100.0, 2000.0, 1900.0, 1700.0, 1500.0, 1300.0, 1100.0, 900.0, 800.0],
        "rpm",
    ),
    # Coolant warming up from ambient towards its operating temperature.
    "coolant_temp": (
        [20.0, 22.0, 25.0, 28.0, 32.0, 36.0, 40.0, 45.0, 50.0, 55.0,
         60.0, 65.0, 70.0, 74.0, 78.0, 81.0, 84.0, 86.0, 88.0, 89.0],
        "degC",
    ),
}
# fmt: on

#: Limits chosen so every channel passes - this is the happy-path demo.
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
]


def write_demo_mdf(path: Path) -> Path:
    signals = [
        Signal(
            samples=np.asarray(samples, dtype=np.float64),
            timestamps=np.asarray(TIMESTAMPS, dtype=np.float64),
            name=name,
            unit=unit,
        )
        for name, (samples, unit) in CHANNELS.items()
    ]
    with MDF(version="4.10") as mdf:
        mdf.append(signals, comment="DataForge demo measurement")
        mdf.save(path, overwrite=True)
    return path


def write_demo_rules(path: Path) -> Path:
    path.write_text(yaml.safe_dump({"checks": RULES}, sort_keys=False))
    return path


def main() -> None:
    print(f"Writing {write_demo_mdf(DEMO_MDF)}")
    print(f"Writing {write_demo_rules(DEMO_RULES)}")


if __name__ == "__main__":
    main()
