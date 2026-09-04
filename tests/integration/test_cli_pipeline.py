"""End-to-end tests that drive the installed `dataforge` console script.

These run the real executable in a subprocess rather than calling `main()`
in-process, so they cover what unit tests cannot: the console-script wrapper
generated from `[project.scripts]`, the exit code as the OS reports it, and the
stdout/stderr split.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.integration

REPORT_KEYS = {"source_file", "rules_yaml", "passed", "check_results"}
CHECK_RESULT_KEYS = {"check_name", "signal_name", "parameters", "passed", "message"}


@pytest.fixture(scope="session")
def dataforge_executable() -> Path:
    """Path to the console script installed alongside the running interpreter."""
    executable = Path(sys.executable).parent / "dataforge"
    if not executable.exists():
        pytest.skip(f"dataforge console script not installed at {executable}")
    return executable


@pytest.fixture
def run_cli(dataforge_executable, tmp_path):
    """Run the CLI in an isolated working directory."""

    def _run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [str(dataforge_executable), *args],
            cwd=str(cwd or tmp_path),
            capture_output=True,
            text=True,
            timeout=120,
        )

    return _run


def read_report(cwd: Path) -> dict:
    """Parse the single summary.json the run should have produced."""
    reports = list(cwd.glob("output/*/summary.json"))
    assert len(reports) == 1, f"expected exactly one report, found {reports}"
    return json.loads(reports[0].read_text())


@pytest.fixture
def passing_run(run_cli, tmp_path, make_mdf, make_rules_yaml, range_rule):
    """Execute a run whose checks all pass, and return (process, payload)."""
    measurement = make_mdf({"speed": [10.0, 20.0, 30.0]}, timestamps=[0.0, 0.5, 1.0])
    rules = make_rules_yaml([range_rule(min_value=0, max_value=100)])

    process = run_cli("-f", str(measurement), "-r", str(rules))

    return process, read_report(tmp_path)


@pytest.fixture
def failing_run(run_cli, tmp_path, make_mdf, make_rules_yaml, range_rule):
    """Execute a run with an out-of-range sample, and return (process, payload)."""
    measurement = make_mdf({"speed": [10.0, 500.0]}, timestamps=[0.0, 1.0])
    rules = make_rules_yaml([range_rule(min_value=0, max_value=100)])

    process = run_cli("-f", str(measurement), "-r", str(rules))

    return process, read_report(tmp_path)


# --- process behaviour ------------------------------------------------------


def test_passing_run_exits_zero(passing_run):
    process, _ = passing_run

    assert process.returncode == 0


def test_failing_run_exits_one(failing_run):
    """CI gates on this: a validation failure must be a non-zero exit."""
    process, _ = failing_run

    assert process.returncode == 1


def test_logs_go_to_stderr_not_stdout(passing_run):
    process, _ = passing_run

    assert "Starting analysis" in process.stderr
    assert "Starting analysis" not in process.stdout


def test_no_traceback_on_a_successful_run(passing_run):
    process, _ = passing_run

    assert "Traceback" not in process.stderr


def test_missing_input_exits_one_without_writing_a_report(
    run_cli, tmp_path, make_rules_yaml, range_rule
):
    rules = make_rules_yaml([range_rule()])

    process = run_cli("-f", str(tmp_path / "absent.mf4"), "-r", str(rules))

    assert process.returncode == 1
    assert not list(tmp_path.glob("output/*/summary.json"))


# --- report structure -------------------------------------------------------


def test_report_is_written(passing_run, tmp_path):
    assert list(tmp_path.glob("output/*/summary.json"))


def test_report_has_exactly_the_expected_top_level_keys(passing_run):
    _, payload = passing_run

    assert set(payload) == REPORT_KEYS


def test_check_result_has_exactly_the_expected_keys(passing_run):
    _, payload = passing_run

    assert set(payload["check_results"][0]) == CHECK_RESULT_KEYS


@pytest.mark.parametrize(
    ("key", "expected_type"),
    [
        pytest.param("source_file", str, id="source-file-is-a-string"),
        pytest.param("rules_yaml", str, id="rules-yaml-is-a-string"),
        pytest.param("passed", bool, id="passed-is-a-bool"),
        pytest.param("check_results", list, id="check-results-is-a-list"),
    ],
)
def test_top_level_field_types(passing_run, key, expected_type):
    _, payload = passing_run

    assert isinstance(payload[key], expected_type)


@pytest.mark.parametrize(
    ("key", "expected_type"),
    [
        pytest.param("check_name", str, id="check-name-is-a-string"),
        pytest.param("signal_name", str, id="signal-name-is-a-string"),
        pytest.param("parameters", dict, id="parameters-is-a-dict"),
        pytest.param("passed", bool, id="passed-is-a-bool"),
        pytest.param("message", str, id="message-is-a-string"),
    ],
)
def test_check_result_field_types(passing_run, key, expected_type):
    _, payload = passing_run

    assert isinstance(payload["check_results"][0][key], expected_type)


def test_report_records_the_input_paths(
    run_cli, tmp_path, make_mdf, make_rules_yaml, range_rule
):
    measurement = make_mdf({"speed": [10.0]})
    rules = make_rules_yaml([range_rule()])

    run_cli("-f", str(measurement), "-r", str(rules))
    payload = read_report(tmp_path)

    assert payload["source_file"] == str(measurement)
    assert payload["rules_yaml"] == str(rules)


@pytest.mark.parametrize(
    ("fixture_name", "expected"),
    [
        pytest.param("passing_run", True, id="all-checks-pass"),
        pytest.param("failing_run", False, id="a-check-fails"),
    ],
)
def test_report_verdict_matches_the_run(request, fixture_name, expected):
    _, payload = request.getfixturevalue(fixture_name)

    assert payload["passed"] is expected


def test_exit_code_and_report_verdict_agree(failing_run):
    """A non-zero exit must never accompany a report claiming success."""
    process, payload = failing_run

    assert (process.returncode == 0) is payload["passed"]


def test_check_result_echoes_the_rule(passing_run):
    _, payload = passing_run

    assert payload["check_results"][0]["check_name"] == "range"
    assert payload["check_results"][0]["signal_name"] == "speed"
    assert payload["check_results"][0]["parameters"] == {
        "min_value": 0,
        "max_value": 100,
    }


def test_failure_message_identifies_the_offending_sample(failing_run):
    _, payload = failing_run

    message = payload["check_results"][0]["message"]
    assert "500.0" in message
    assert "1.0" in message


@pytest.mark.parametrize(
    "rule_count",
    [
        pytest.param(1, id="one-rule"),
        pytest.param(3, id="three-rules"),
    ],
)
def test_every_rule_produces_a_check_result(
    run_cli, tmp_path, make_mdf, make_rules_yaml, range_rule, rule_count
):
    channels = {f"ch{i}": [10.0] for i in range(rule_count)}
    measurement = make_mdf(channels)
    rules = make_rules_yaml(
        [range_rule(channel=name, min_value=0, max_value=100) for name in channels]
    )

    run_cli("-f", str(measurement), "-r", str(rules))
    payload = read_report(tmp_path)

    assert len(payload["check_results"]) == rule_count
    assert [c["signal_name"] for c in payload["check_results"]] == list(channels)


def test_mixed_outcomes_are_reported_per_check(
    run_cli, tmp_path, make_mdf, make_rules_yaml, range_rule
):
    measurement = make_mdf({"speed": [10.0], "rpm": [9000.0]})
    rules = make_rules_yaml(
        [
            range_rule(channel="speed", min_value=0, max_value=100),
            range_rule(channel="rpm", min_value=0, max_value=100),
        ]
    )

    process = run_cli("-f", str(measurement), "-r", str(rules))
    payload = read_report(tmp_path)

    assert [check["passed"] for check in payload["check_results"]] == [True, False]
    assert payload["passed"] is False
    assert process.returncode == 1


def test_run_directory_is_named_after_the_measurement_file(
    run_cli, tmp_path, make_mdf, make_rules_yaml, range_rule
):
    measurement = make_mdf({"speed": [10.0]}, filename="drive_cycle.mf4")
    rules = make_rules_yaml([range_rule()])

    run_cli("-f", str(measurement), "-r", str(rules))

    report = next(tmp_path.glob("output/*/summary.json"))
    assert report.parent.name.startswith("drive_cycle_")


# --- options ----------------------------------------------------------------


def test_log_file_captures_the_run(
    run_cli, tmp_path, make_mdf, make_rules_yaml, range_rule
):
    measurement = make_mdf({"speed": [10.0]})
    rules = make_rules_yaml([range_rule()])
    log_file = tmp_path / "run.log"

    run_cli("-f", str(measurement), "-r", str(rules), "-log", str(log_file))

    assert "Starting analysis" in log_file.read_text()


def test_verbose_adds_debug_output(
    run_cli, tmp_path, make_mdf, make_rules_yaml, range_rule
):
    measurement = make_mdf({"speed": [10.0]})
    rules = make_rules_yaml([range_rule()])

    quiet = run_cli("-f", str(measurement), "-r", str(rules))
    verbose = run_cli("-f", str(measurement), "-r", str(rules), "-v")

    assert "DEBUG" not in quiet.stderr
    assert "DEBUG" in verbose.stderr


# --- the bundled files ------------------------------------------------------


def test_bundled_examples_run_and_pass(run_cli, tmp_path):
    """The demo shipped in `examples/` must work with no setup.

    These are the only measurement files copied into the Docker image, so a
    failure here means an image user has nothing runnable. Unlike the
    regression fixture, the demo is expected to pass - that is the whole point
    of it as a first-run experience.
    """
    examples = Path(__file__).resolve().parents[2] / "examples"
    measurement = examples / "demo.mf4"
    rules = examples / "demo_rules.yaml"
    if not measurement.exists() or not rules.exists():
        pytest.skip("bundled example files are absent")

    process = run_cli("-f", str(measurement), "-r", str(rules), cwd=tmp_path)
    payload = read_report(tmp_path)

    assert process.returncode == 0
    assert payload["passed"] is True
    assert set(payload) == REPORT_KEYS
    assert [c["signal_name"] for c in payload["check_results"]] == [
        "speed",
        "engine_rpm",
        "coolant_temp",
    ]


# --- the committed fixture --------------------------------------------------


def test_repository_fixture_and_rules_still_work(run_cli, tmp_path):
    """Runs the exact command documented in the README against the committed
    fixture, writing output into a temp directory so the repo stays clean.

    The fixture carries an injected out-of-range spike, so a *failing* run is
    the documented behaviour. What this asserts is that the bundled files are
    still wired up correctly and produce a well-formed report - the specific
    check outcomes are the regression suite's job, not this test's.
    """
    fixtures = Path(__file__).resolve().parents[1] / "regression" / "fixtures"
    measurement = fixtures / "regression_v1.mf4"
    rules = fixtures / "regression_v1_rules.yaml"
    if not measurement.exists() or not rules.exists():
        pytest.skip("committed fixture or rules file is absent")

    process = run_cli("-f", str(measurement), "-r", str(rules), cwd=tmp_path)
    payload = read_report(tmp_path)

    assert process.returncode == 1
    assert set(payload) == REPORT_KEYS
    assert payload["passed"] is False
    assert len(payload["check_results"]) == len(yaml.safe_load(rules.read_text())["checks"])
