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
            source_file=Path("data/sample/sample_speed.mf4"),
            check_results=[
                CheckResult(
                    check_name="range",
                    signal_name="speed",
                    parameters={"min_value": 0, "max_value": 100},
                    passed=passed,
                    message="ok" if passed else "out of range",
                )
            ],
            rules_yaml=Path("data/rules.yaml"),
        )

    return _make


@pytest.fixture
def written_payload(tmp_path, monkeypatch, analysis_result):
    """Generate a report in an isolated cwd and return (payload, report_path)."""

    def _generate(passed: bool = True):
        monkeypatch.chdir(tmp_path)
        JSONReporter().generate(analysis_result(passed))
        reports = list(tmp_path.glob("output/*/summary.json"))
        assert len(reports) == 1, f"expected exactly one report, found {reports}"
        return json.loads(reports[0].read_text()), reports[0]

    return _generate


def test_writes_a_summary_json(written_payload):
    _, report_path = written_payload()

    assert report_path.exists()


def test_run_directory_is_named_after_the_source_file(written_payload):
    _, report_path = written_payload()

    assert report_path.parent.name.startswith("sample_speed_")


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        pytest.param("source_file", "data/sample/sample_speed.mf4", id="source-file"),
        pytest.param("rules_yaml", "data/rules.yaml", id="rules-yaml"),
    ],
)
def test_payload_records_the_inputs(written_payload, key, expected):
    payload, _ = written_payload()

    assert payload[key] == expected


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


def test_creates_the_output_directory_when_absent(tmp_path, monkeypatch, analysis_result):
    monkeypatch.chdir(tmp_path)
    assert not (tmp_path / "output").exists()

    JSONReporter().generate(analysis_result())

    assert (tmp_path / "output").is_dir()


def test_is_a_reporter():
    assert isinstance(JSONReporter(), Reporter)
