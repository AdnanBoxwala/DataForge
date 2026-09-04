"""Regression tests: the pipeline's output must match a committed baseline.

A failure here is not automatically a bug in the test. It means the report
changed, and someone must decide which of two things is true:

  * the change under review is wrong, and the code should be fixed, or
  * the change is intended, and the baseline should be regenerated and reviewed
    as part of the same commit:

        uv run python tests/regression/generate_baseline.py

Never regenerate the baseline simply to turn this suite green.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from baseline_utils import (
    BASELINE_JSON,
    DROPOUT_TIMEBASE,
    FIXTURE_MDF,
    FIXTURE_RULES,
    TIMEBASE,
    normalise_report,
)

from dataforge.ingestion import MDFIngestor

pytestmark = pytest.mark.regression


@pytest.fixture(scope="session")
def baseline() -> dict:
    if not BASELINE_JSON.exists():
        pytest.fail(
            f"Baseline missing at {BASELINE_JSON}. "
            "Generate it with 'uv run python tests/regression/generate_baseline.py'."
        )
    return json.loads(BASELINE_JSON.read_text())


@pytest.fixture
def pipeline_output(tmp_path) -> tuple[subprocess.CompletedProcess, dict]:
    """Run the committed fixture through the real CLI in an isolated directory."""
    for artefact in (FIXTURE_MDF, FIXTURE_RULES):
        if not artefact.exists():
            pytest.fail(
                f"Regression fixture missing at {artefact}. "
                "Generate it with 'uv run python tests/regression/generate_baseline.py'."
            )

    executable = Path(sys.executable).parent / "dataforge"
    if not executable.exists():
        pytest.skip(f"dataforge console script not installed at {executable}")

    process = subprocess.run(
        [str(executable), "-f", str(FIXTURE_MDF), "-r", str(FIXTURE_RULES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=120,
    )

    reports = list(tmp_path.glob("output/*/summary.json"))
    assert len(reports) == 1, f"expected exactly one report, found {reports}"
    return process, normalise_report(json.loads(reports[0].read_text()))


# --- the baseline comparison ------------------------------------------------


def test_report_matches_the_baseline(pipeline_output, baseline):
    """The whole-report assertion. Everything below narrows down a failure."""
    _, actual = pipeline_output

    assert actual == baseline


def test_overall_verdict_matches_the_baseline(pipeline_output, baseline):
    _, actual = pipeline_output

    assert actual["passed"] == baseline["passed"]


def test_exit_code_agrees_with_the_baseline_verdict(pipeline_output, baseline):
    """The baseline records a failing analysis, so the CLI must exit non-zero."""
    process, _ = pipeline_output

    assert (process.returncode == 0) is baseline["passed"]


def test_check_count_matches_the_baseline(pipeline_output, baseline):
    _, actual = pipeline_output

    assert len(actual["check_results"]) == len(baseline["check_results"])


def test_check_order_matches_the_baseline(pipeline_output, baseline):
    """Results are reported in rules-file order; reordering is a regression."""
    _, actual = pipeline_output

    assert [c["signal_name"] for c in actual["check_results"]] == [
        c["signal_name"] for c in baseline["check_results"]
    ]


@pytest.mark.parametrize(
    "signal_name",
    ["speed", "engine_rpm", "coolant_temp", "wheel_speed"],
)
def test_each_check_matches_the_baseline(pipeline_output, baseline, signal_name):
    """Per-check comparison, so a failure names the channel that drifted."""
    _, actual = pipeline_output

    def _by_name(payload: dict) -> dict:
        matches = [c for c in payload["check_results"] if c["signal_name"] == signal_name]
        assert len(matches) == 1, f"expected one result for {signal_name}, got {matches}"
        return matches[0]

    assert _by_name(actual) == _by_name(baseline)


# --- what the baseline is asserting, stated explicitly ----------------------


def test_the_injected_spike_is_the_only_failure(pipeline_output):
    """Guards the fault the fixture was built around.

    `engine_rpm` carries a deliberate out-of-range spike; every other channel is
    within limits. If this changes, either the check or the fixture drifted.
    """
    _, actual = pipeline_output

    failed = [c["signal_name"] for c in actual["check_results"] if not c["passed"]]

    assert failed == ["engine_rpm"]


def test_the_failure_message_pinpoints_the_spike(pipeline_output):
    _, actual = pipeline_output

    message = next(
        c["message"] for c in actual["check_results"] if c["signal_name"] == "engine_rpm"
    )

    assert "9500.0" in message
    assert "2.0" in message


def test_a_frozen_signal_is_not_yet_detected(pipeline_output):
    """`coolant_temp` never changes, which a stale-signal check should flag.

    No such check exists yet, so it passes. When one is added this will fail,
    which is the intended prompt to update the baseline deliberately.
    """
    _, actual = pipeline_output

    coolant = next(
        c for c in actual["check_results"] if c["signal_name"] == "coolant_temp"
    )

    assert coolant["passed"] is True


def test_dropped_samples_do_not_break_the_pipeline(pipeline_output):
    """`wheel_speed` has a gap in its timebase; ingestion must still succeed."""
    _, actual = pipeline_output

    wheel = next(
        c for c in actual["check_results"] if c["signal_name"] == "wheel_speed"
    )

    assert wheel["passed"] is True


# --- fixture integrity ------------------------------------------------------


def test_fixture_contains_the_expected_channels():
    """Catches an accidental or unreviewed regeneration of the `.mf4`."""
    signal_set = MDFIngestor().load(FIXTURE_MDF)

    assert set(signal_set.signals) == {
        "speed",
        "engine_rpm",
        "coolant_temp",
        "wheel_speed",
    }


@pytest.mark.parametrize(
    ("channel", "expected_length"),
    [
        pytest.param("speed", len(TIMEBASE), id="speed"),
        pytest.param("engine_rpm", len(TIMEBASE), id="engine-rpm"),
        pytest.param("coolant_temp", len(TIMEBASE), id="coolant-temp"),
        pytest.param("wheel_speed", len(DROPOUT_TIMEBASE), id="wheel-speed-dropout"),
    ],
)
def test_fixture_sample_counts_are_unchanged(channel, expected_length):
    signal = MDFIngestor().load(FIXTURE_MDF).get(channel)

    assert len(signal.samples) == expected_length
    assert len(signal.timestamps) == expected_length


def test_fixture_retains_the_injected_spike():
    signal = MDFIngestor().load(FIXTURE_MDF).get("engine_rpm")

    assert signal.samples.max() == 9500.0


def test_fixture_retains_the_frozen_stretch():
    signal = MDFIngestor().load(FIXTURE_MDF).get("coolant_temp")

    assert len(set(signal.samples.tolist())) == 1


def test_fixture_retains_the_timebase_gap():
    """The dropped-sample gap is the fault; a uniform timebase would erase it."""
    signal = MDFIngestor().load(FIXTURE_MDF).get("wheel_speed")

    gaps = signal.timestamps[1:] - signal.timestamps[:-1]

    assert gaps.max() > 2 * gaps.min()
