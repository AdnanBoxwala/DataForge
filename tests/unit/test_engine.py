"""Unit tests for `dataforge.engine.engine`."""

import pytest

from dataforge.engine import run
from dataforge.enums.result import Result


@pytest.mark.parametrize(
    ("samples", "expected"),
    [
        pytest.param([10.0, 20.0, 30.0], Result.PASS, id="all-checks-pass"),
        pytest.param([0.0, 100.0], Result.PASS, id="samples-on-the-bounds"),
        pytest.param([10.0, 500.0], Result.FAIL, id="a-sample-exceeds-maximum"),
        pytest.param([-5.0, 10.0], Result.FAIL, id="a-sample-is-below-minimum"),
    ],
)
def test_verdict_reflects_check_outcomes(
    tmp_path, monkeypatch, make_mdf, make_rules_yaml, range_rule, samples, expected
):
    monkeypatch.chdir(tmp_path)
    measurement = make_mdf({"speed": samples})
    rules = make_rules_yaml([range_rule(min_value=0, max_value=100)])

    assert run(measurement, rules) is expected


def test_writes_a_report(tmp_path, monkeypatch, make_mdf, make_rules_yaml, range_rule):
    monkeypatch.chdir(tmp_path)
    measurement = make_mdf({"speed": [10.0]})

    run(measurement, make_rules_yaml([range_rule()]))

    assert list(tmp_path.glob("output/*/summary.json"))


def test_every_rule_is_evaluated(
    tmp_path, monkeypatch, make_mdf, make_rules_yaml, range_rule
):
    """The second rule is the failing one, so it must have been run."""
    monkeypatch.chdir(tmp_path)
    measurement = make_mdf({"speed": [10.0], "rpm": [900.0]})
    rules = make_rules_yaml(
        [
            range_rule(channel="speed", min_value=0, max_value=100),
            range_rule(channel="rpm", min_value=0, max_value=100),
        ]
    )

    assert run(measurement, rules) is Result.FAIL


def test_no_rules_yields_pass(tmp_path, monkeypatch, make_mdf, make_rules_yaml):
    monkeypatch.chdir(tmp_path)
    measurement = make_mdf({"speed": [10.0]})

    assert run(measurement, make_rules_yaml([])) is Result.PASS


@pytest.mark.parametrize(
    ("missing", "match"),
    [
        pytest.param("measurement", "does not exist", id="missing-measurement-file"),
        pytest.param("rules", "does not exist", id="missing-rules-file"),
    ],
)
def test_missing_input_files_raise(
    tmp_path, monkeypatch, make_mdf, make_rules_yaml, range_rule, missing, match
):
    monkeypatch.chdir(tmp_path)
    measurement = (
        tmp_path / "absent.mf4"
        if missing == "measurement"
        else make_mdf({"speed": [10.0]})
    )
    rules = (
        tmp_path / "absent.yaml"
        if missing == "rules"
        else make_rules_yaml([range_rule()])
    )

    with pytest.raises(FileNotFoundError, match=match):
        run(measurement, rules)


def test_bad_rules_path_fails_before_ingestion(tmp_path, monkeypatch):
    """Rules load first, so a bad rules path is reported even when the
    measurement file is also unreadable - it must not cost an MDF parse.
    """
    monkeypatch.chdir(tmp_path)
    corrupt = tmp_path / "corrupt.mf4"
    corrupt.write_bytes(b"not an MDF file")

    with pytest.raises(FileNotFoundError, match="rules"):
        run(corrupt, tmp_path / "absent.yaml")


def test_unsupported_measurement_format_raises(
    tmp_path, monkeypatch, make_rules_yaml, range_rule
):
    monkeypatch.chdir(tmp_path)
    measurement = tmp_path / "measurement.csv"
    measurement.write_text("time,speed\n0,10\n")

    with pytest.raises(ValueError, match="No ingestor registered"):
        run(measurement, make_rules_yaml([range_rule()]))


@pytest.mark.parametrize(
    ("rule", "match"),
    [
        pytest.param(
            {"type": "no_such_check", "channel": "speed", "parameters": {}},
            "is not registered",
            id="unregistered-check-type",
        ),
        pytest.param(
            {
                "type": "range",
                "channel": "rpm",
                "parameters": {"min_value": 0, "max_value": 100},
            },
            "not found",
            id="channel-absent-from-file",
        ),
    ],
)
def test_invalid_rules_raise_key_error(
    tmp_path, monkeypatch, make_mdf, make_rules_yaml, rule, match
):
    monkeypatch.chdir(tmp_path)
    measurement = make_mdf({"speed": [10.0]})

    with pytest.raises(KeyError, match=match):
        run(measurement, make_rules_yaml([rule]))
