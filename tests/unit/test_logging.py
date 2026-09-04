"""Unit tests for `dataforge.logging`."""

import logging

import pytest

from dataforge.logging import configure_logging


@pytest.mark.parametrize(
    ("verbose", "expected_level"),
    [
        pytest.param(False, logging.INFO, id="default-is-info"),
        pytest.param(True, logging.DEBUG, id="verbose-is-debug"),
    ],
)
def test_verbosity_selects_the_root_level(restore_root_logger, verbose, expected_level):
    configure_logging(verbose=verbose)

    assert logging.getLogger().level == expected_level


@pytest.mark.parametrize(
    ("verbose", "level", "should_appear"),
    [
        pytest.param(False, "debug", False, id="debug-suppressed-by-default"),
        pytest.param(False, "info", True, id="info-shown-by-default"),
        pytest.param(False, "warning", True, id="warning-shown-by-default"),
        pytest.param(True, "debug", True, id="debug-shown-when-verbose"),
    ],
)
def test_messages_are_filtered_by_level(
    restore_root_logger, capsys, verbose, level, should_appear
):
    configure_logging(verbose=verbose)

    getattr(logging.getLogger("dataforge.test"), level)("marker text")

    assert ("marker text" in capsys.readouterr().err) is should_appear


def test_logs_to_stderr_not_stdout(restore_root_logger, capsys):
    """Logs belong on stderr so stdout stays reserved for machine-readable output."""
    configure_logging()

    logging.getLogger("dataforge.test").info("hello from the test")

    captured = capsys.readouterr()
    assert "hello from the test" in captured.err
    assert captured.out == ""


def test_log_file_is_created_and_written(tmp_path, restore_root_logger):
    log_file = tmp_path / "run.log"

    configure_logging(log_file=log_file)
    logging.getLogger("dataforge.test").info("written to file")
    logging.shutdown()

    assert "written to file" in log_file.read_text()


def test_log_file_also_keeps_stderr_output(tmp_path, restore_root_logger, capsys):
    configure_logging(log_file=tmp_path / "run.log")

    logging.getLogger("dataforge.test").info("goes to both")

    assert "goes to both" in capsys.readouterr().err


@pytest.mark.parametrize(
    "expected_fragment",
    [
        pytest.param("WARNING", id="level-name"),
        pytest.param("dataforge.test", id="logger-name"),
        pytest.param("formatted", id="message"),
    ],
)
def test_output_format_includes_context(restore_root_logger, capsys, expected_fragment):
    configure_logging()

    logging.getLogger("dataforge.test").warning("formatted")

    assert expected_fragment in capsys.readouterr().err


def test_can_be_reconfigured(restore_root_logger):
    """`force=True` means a second call replaces the first configuration."""
    configure_logging(verbose=True)
    configure_logging(verbose=False)

    assert logging.getLogger().level == logging.INFO
