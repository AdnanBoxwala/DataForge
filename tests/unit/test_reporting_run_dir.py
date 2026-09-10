"""Unit tests for `dataforge.reporting.run_dir`."""

import re
from pathlib import Path

import pytest

from dataforge.reporting.run_dir import (
    DEFAULT_LOG_NAME,
    INPUTS_DIR_NAME,
    archive_inputs,
    create_run_directory,
)

RUN_NAME_PATTERN = re.compile(r"^drive_cycle_\d{8}_\d{6}Z$")


# --- create_run_directory ---------------------------------------------------


def test_creates_the_directory(tmp_path):
    run_dir = create_run_directory(Path("drive_cycle.mf4"), base_dir=tmp_path)

    assert run_dir.is_dir()


def test_name_combines_the_measurement_stem_with_a_utc_timestamp(tmp_path):
    run_dir = create_run_directory(Path("drive_cycle.mf4"), base_dir=tmp_path)

    assert RUN_NAME_PATTERN.match(run_dir.name), run_dir.name


def test_uses_only_the_stem_not_the_whole_path(tmp_path):
    run_dir = create_run_directory(
        Path("/some/where/drive_cycle.mf4"), base_dir=tmp_path
    )

    assert run_dir.name.startswith("drive_cycle_")


def test_sits_inside_the_base_directory(tmp_path):
    base = tmp_path / "reports"

    run_dir = create_run_directory(Path("drive_cycle.mf4"), base_dir=base)

    assert run_dir.parent == base


def test_creates_missing_parent_directories(tmp_path):
    base = tmp_path / "deeply" / "nested" / "output"

    assert create_run_directory(Path("drive_cycle.mf4"), base_dir=base).is_dir()


def test_measurement_file_need_not_exist(tmp_path):
    """The directory is created before the inputs are validated."""
    run_dir = create_run_directory(tmp_path / "absent.mf4", base_dir=tmp_path)

    assert run_dir.is_dir()


def test_defaults_to_an_output_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    run_dir = create_run_directory(Path("drive_cycle.mf4"))

    assert run_dir.parent == Path("output")


# --- archive_inputs ---------------------------------------------------------


@pytest.fixture
def inputs(tmp_path):
    measurement = tmp_path / "drive_cycle.mf4"
    measurement.write_bytes(b"measurement bytes")
    rules = tmp_path / "rules.yaml"
    rules.write_text("checks: []\n")
    return measurement, rules


def test_copies_every_input_into_the_inputs_subdirectory(tmp_path, inputs):
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    archived = archive_inputs(run_dir, *inputs)

    assert [path.parent for path in archived] == [run_dir / INPUTS_DIR_NAME] * 2
    assert {path.name for path in archived} == {"drive_cycle.mf4", "rules.yaml"}


def test_copies_preserve_content(tmp_path, inputs):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    measurement, rules = inputs

    archive_inputs(run_dir, measurement, rules)

    inputs_dir = run_dir / INPUTS_DIR_NAME
    assert (inputs_dir / measurement.name).read_bytes() == measurement.read_bytes()
    assert (inputs_dir / rules.name).read_text() == rules.read_text()


def test_originals_are_left_in_place(tmp_path, inputs):
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    archive_inputs(run_dir, *inputs)

    assert all(path.exists() for path in inputs)


def test_creates_the_inputs_directory(tmp_path, inputs):
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    archive_inputs(run_dir, *inputs)

    assert (run_dir / INPUTS_DIR_NAME).is_dir()


def test_missing_inputs_are_skipped_rather_than_raising(tmp_path, inputs):
    """The clearer error belongs to whichever component actually needs the file."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    measurement, _ = inputs

    archived = archive_inputs(run_dir, measurement, tmp_path / "absent.yaml")

    assert [path.name for path in archived] == ["drive_cycle.mf4"]


def test_no_inputs_still_creates_the_directory(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    assert archive_inputs(run_dir) == []
    assert (run_dir / INPUTS_DIR_NAME).is_dir()


def test_default_log_name_is_a_bare_filename():
    """It is joined onto the run directory, so it must not be a path."""
    assert Path(DEFAULT_LOG_NAME).name == DEFAULT_LOG_NAME


def test_concurrent_runs_get_separate_directories(tmp_path):
    """Second-resolution timestamps collide; each run still needs its own home."""
    measurement = Path("drive_cycle.mf4")

    first = create_run_directory(measurement, base_dir=tmp_path)
    second = create_run_directory(measurement, base_dir=tmp_path)
    third = create_run_directory(measurement, base_dir=tmp_path)

    assert len({first, second, third}) == 3
    assert all(path.is_dir() for path in (first, second, third))


def test_a_collision_is_disambiguated_by_suffix(tmp_path):
    first = create_run_directory(Path("drive_cycle.mf4"), base_dir=tmp_path)
    second = create_run_directory(Path("drive_cycle.mf4"), base_dir=tmp_path)

    assert second.name == f"{first.name}_2"
