"""Unit tests for `dataforge.structs.result`."""

from pathlib import Path

import pytest

from dataforge.structs.result import AnalysisResult, CheckResult


def _check_result(passed: bool = True) -> CheckResult:
    return CheckResult(
        check_name="range",
        signal_name="speed",
        parameters={"min_value": 0, "max_value": 100},
        passed=passed,
        message="message",
    )


def test_check_result_to_dict_contains_every_field():
    assert _check_result().to_dict() == {
        "check_name": "range",
        "signal_name": "speed",
        "parameters": {"min_value": 0, "max_value": 100},
        "passed": True,
        "message": "message",
    }


@pytest.mark.parametrize(
    ("outcomes", "expected"),
    [
        pytest.param([True], True, id="single-pass"),
        pytest.param([False], False, id="single-fail"),
        pytest.param([True, True], True, id="all-pass"),
        pytest.param([True, False], False, id="one-of-two-fails"),
        pytest.param([False, False], False, id="all-fail"),
        pytest.param([True, True, False], False, id="last-of-three-fails"),
        # `all([])` is True: an empty rules file currently reports success
        # rather than flagging that nothing was validated.
        pytest.param([], True, id="no-checks-passes-vacuously"),
    ],
)
def test_analysis_passed_aggregates_check_outcomes(outcomes, expected):
    result = AnalysisResult(
        source_file=Path("measurement.mf4"),
        check_results=[_check_result(passed) for passed in outcomes],
        rules_yaml=Path("rules.yaml"),
    )

    assert result.passed is expected
