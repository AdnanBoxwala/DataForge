"""Unit tests for `dataforge.cli`."""

import pytest

from dataforge.cli import main
from dataforge.reporting import DEFAULT_LOG_NAME

PASSING_SAMPLES = [10.0, 20.0]
FAILING_SAMPLES = [10.0, 500.0]


def _run_cli(monkeypatch, *args: str) -> int:
    """Invoke `main()` with the given argv and return its exit code."""
    monkeypatch.setattr("sys.argv", ["dataforge", *args])
    with pytest.raises(SystemExit) as exc_info:
        main()
    return exc_info.value.code


def _run_dir(tmp_path):
    """The single run directory the CLI created under tmp_path/output."""
    run_dirs = [path for path in (tmp_path / "output").iterdir() if path.is_dir()]
    assert len(run_dirs) == 1, f"expected exactly one run directory, found {run_dirs}"
    return run_dirs[0]


@pytest.fixture
def cli(
    tmp_path, monkeypatch, restore_root_logger, make_mdf, make_rules_yaml, range_rule
):
    """Return a runner that sets up inputs in an isolated cwd and invokes the CLI."""

    def _run(*extra_args: str, samples=PASSING_SAMPLES, measurement=None) -> int:
        monkeypatch.chdir(tmp_path)
        measurement_path = (
            measurement if measurement is not None else make_mdf({"speed": samples})
        )
        rules = make_rules_yaml([range_rule(min_value=0, max_value=100)])
        return _run_cli(
            monkeypatch, "-f", str(measurement_path), "-r", str(rules), *extra_args
        )

    return _run


@pytest.mark.parametrize(
    ("samples", "expected_code"),
    [
        pytest.param(PASSING_SAMPLES, 0, id="validation-passes"),
        pytest.param(FAILING_SAMPLES, 1, id="validation-fails"),
    ],
)
def test_exit_code_reflects_the_verdict(cli, samples, expected_code):
    assert cli(samples=samples) == expected_code


def test_exits_one_when_the_measurement_file_is_missing(cli, tmp_path):
    assert cli(measurement=tmp_path / "absent.mf4") == 1


def test_reports_the_error_without_a_traceback(cli, tmp_path, capsys):
    cli(measurement=tmp_path / "absent.mf4")

    stderr = capsys.readouterr().err
    assert "does not exist" in stderr
    assert "Traceback" not in stderr


def test_unexpected_errors_are_logged_with_a_traceback(cli, monkeypatch, capsys):
    def _boom(*args, **kwargs):
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr("dataforge.cli.run", _boom)

    assert cli() == 1
    assert "Traceback" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("file_flag", "rules_flag"),
    [
        pytest.param("-f", "-r", id="short-flags"),
        pytest.param("--measurement-file", "--rules", id="long-flags"),
    ],
)
def test_both_option_spellings_are_accepted(
    tmp_path,
    monkeypatch,
    restore_root_logger,
    make_mdf,
    make_rules_yaml,
    range_rule,
    file_flag,
    rules_flag,
):
    monkeypatch.chdir(tmp_path)
    measurement = make_mdf({"speed": PASSING_SAMPLES})
    rules = make_rules_yaml([range_rule(min_value=0, max_value=100)])

    exit_code = _run_cli(
        monkeypatch, file_flag, str(measurement), rules_flag, str(rules)
    )

    assert exit_code == 0


@pytest.mark.parametrize(
    ("extra_args", "debug_expected"),
    [
        pytest.param([], False, id="default-is-info"),
        pytest.param(["-v"], True, id="short-verbose-flag"),
        pytest.param(["--verbose"], True, id="long-verbose-flag"),
    ],
)
def test_verbose_controls_debug_output(cli, capsys, extra_args, debug_expected):
    cli(*extra_args)

    assert ("DEBUG" in capsys.readouterr().err) is debug_expected


def test_a_log_file_is_written_by_default(cli, tmp_path):
    """No flag needed: every run leaves its log beside the report."""
    cli()

    log_file = _run_dir(tmp_path) / DEFAULT_LOG_NAME

    assert log_file.is_file()
    assert "Starting analysis" in log_file.read_text()


def test_the_log_sits_beside_the_summary(cli, tmp_path):
    cli()

    run_dir = _run_dir(tmp_path)

    assert (run_dir / DEFAULT_LOG_NAME).parent == (run_dir / "summary.json").parent


@pytest.mark.parametrize(
    "log_flag",
    [
        pytest.param("-log", id="short-flag"),
        pytest.param("--log-file", id="long-flag"),
    ],
)
def test_log_file_argument_renames_the_log(cli, tmp_path, log_flag):
    cli(log_flag, "analysis.log")

    run_dir = _run_dir(tmp_path)

    assert (run_dir / "analysis.log").is_file()
    assert not (run_dir / DEFAULT_LOG_NAME).exists()
    assert "Starting analysis" in (run_dir / "analysis.log").read_text()


def test_an_absolute_log_path_is_used_as_given(cli, tmp_path):
    """The escape hatch for writing the log outside the run directory."""
    log_file = tmp_path / "elsewhere" / "run.log"
    log_file.parent.mkdir()

    cli("--log-file", str(log_file))

    assert "Starting analysis" in log_file.read_text()
    assert not (_run_dir(tmp_path) / DEFAULT_LOG_NAME).exists()


def test_the_inputs_are_archived_beside_the_report(cli, tmp_path):
    cli()

    inputs_dir = _run_dir(tmp_path) / "inputs"

    assert sorted(path.name for path in inputs_dir.iterdir()) == [
        "measurement.mf4",
        "rules.yaml",
    ]


def test_archived_inputs_match_the_originals(cli, tmp_path):
    cli()

    archived = _run_dir(tmp_path) / "inputs" / "measurement.mf4"

    assert archived.read_bytes() == (tmp_path / "measurement.mf4").read_bytes()


def test_a_failed_run_still_leaves_a_log(cli, tmp_path):
    """The log is what explains the failure, so it must survive one."""
    assert cli(measurement=tmp_path / "absent.mf4") == 1

    log_text = (_run_dir(tmp_path) / DEFAULT_LOG_NAME).read_text()

    assert "does not exist" in log_text


@pytest.mark.parametrize(
    "args",
    [
        pytest.param([], id="no-arguments"),
        pytest.param(["-f", "measurement.mf4"], id="rules-missing"),
        pytest.param(["-r", "rules.yaml"], id="measurement-file-missing"),
    ],
)
def test_missing_required_arguments_exit_with_usage_error(monkeypatch, args):
    assert _run_cli(monkeypatch, *args) == 2
