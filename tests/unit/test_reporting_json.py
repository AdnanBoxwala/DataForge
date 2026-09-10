"""Unit tests for `dataforge.reporting.json_report`."""

import json
from pathlib import Path

import pytest

from dataforge.reporting.base import Reporter
from dataforge.reporting.json_report import JSONReporter
from dataforge.structs.result import AnalysisResult, CheckResult


@pytest.fixture
def analysis_result():
    def _make(passed: bool = True) -> AnalysisResult:
        return AnalysisResult(
            source_file=Path("measurements/drive_cycle.mf4"),
            check_results=[
                CheckResult(
                    check_name="range",
                    signal_name="speed",
                    parameters={"min_value": 0, "max_value": 100},
                    passed=passed,
                    message="ok" if passed else "out of range",
                )
            ],
            rules_yaml=Path("config/rules.yaml"),
        )

    return _make


@pytest.fixture
def run_dir(tmp_path) -> Path:
    """An existing run directory, as the CLI would have created."""
    path = tmp_path / "output" / "drive_cycle_20260101_000000Z"
    path.mkdir(parents=True)
    return path


@pytest.fixture
def written_payload(run_dir, analysis_result):
    """Generate a report and return (payload, report_path)."""

    def _generate(passed: bool = True):
        report_path = JSONReporter(run_dir).generate(analysis_result(passed))
        return json.loads(report_path.read_text()), report_path

    return _generate


def test_writes_summary_json_into_the_run_directory(written_payload, run_dir):
    _, report_path = written_payload()

    assert report_path == run_dir / "summary.json"
    assert report_path.exists()


def test_generate_returns_the_report_path(run_dir, analysis_result):
    """The Reporter contract declares a Path, and callers rely on it."""
    assert JSONReporter(run_dir).generate(analysis_result()) == run_dir / "summary.json"


def test_creates_the_run_directory_when_absent(tmp_path, analysis_result):
    """The CLI creates it first, but a direct caller need not."""
    absent = tmp_path / "output" / "not_yet_there"

    report_path = JSONReporter(absent).generate(analysis_result())

    assert absent.is_dir()
    assert report_path.exists()


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        pytest.param("source_file", "measurements/drive_cycle.mf4", id="source-file"),
        pytest.param("rules_yaml", "config/rules.yaml", id="rules-yaml"),
    ],
)
def test_payload_records_the_inputs(written_payload, key, expected):
    payload, _ = written_payload()

    assert Path(payload[key]) == Path(expected)


@pytest.mark.parametrize(
    "passed",
    [
        pytest.param(True, id="passing-analysis"),
        pytest.param(False, id="failing-analysis"),
    ],
)
def test_payload_records_the_overall_verdict(written_payload, passed):
    payload, _ = written_payload(passed)

    assert payload["passed"] is passed


def test_payload_includes_each_check_result(written_payload):
    payload, _ = written_payload()

    assert payload["check_results"] == [
        {
            "check_name": "range",
            "signal_name": "speed",
            "parameters": {"min_value": 0, "max_value": 100},
            "passed": True,
            "message": "ok",
        }
    ]


def test_is_a_reporter(run_dir):
    assert isinstance(JSONReporter(run_dir), Reporter)
