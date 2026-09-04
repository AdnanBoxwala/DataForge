"""Unit tests for `dataforge.validation.base`."""

import pytest

from dataforge.structs.result import CheckResult
from dataforge.validation.base import _CHECK_REGISTRY, get_check, register_check
from dataforge.validation.checks import range_check


def _stub_check(channel: str, signals, **kwargs) -> CheckResult:
    return CheckResult(
        check_name="stub",
        signal_name=channel,
        parameters={},
        passed=True,
        message="ok",
    )


def test_range_check_is_registered_under_its_name():
    assert get_check("range") is range_check


def test_range_check_is_registered_on_package_import():
    """Regression test: the registry is populated by an import side effect.

    `dataforge.validation.__init__` imports `range_check` purely so the
    `@register_check` decorator runs. Removing that seemingly unused import
    empties the registry and every rule fails to resolve.
    """
    import dataforge.validation  # noqa: F401  (import under test)

    assert "range" in _CHECK_REGISTRY


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("does_not_exist", id="unknown-name"),
        pytest.param("Range", id="wrong-case"),
        pytest.param("", id="empty-name"),
    ],
)
def test_unknown_check_raises_key_error(name):
    with pytest.raises(KeyError, match="is not registered"):
        get_check(name)


@pytest.mark.parametrize(
    "pattern",
    [
        pytest.param("is not registered", id="states-the-problem"),
        pytest.param("range", id="lists-available-checks"),
    ],
)
def test_unknown_check_error_is_actionable(pattern):
    with pytest.raises(KeyError, match=pattern):
        get_check("does_not_exist")


def test_register_check_adds_to_registry(isolated_registries):
    register_check("always_passes")(_stub_check)

    assert get_check("always_passes") is _stub_check


def test_register_check_returns_the_function_unchanged(isolated_registries):
    assert register_check("noop")(_stub_check) is _stub_check


def test_registering_an_existing_name_overwrites_it(isolated_registries):
    """Documents that registration is last-one-wins, with no collision warning."""
    register_check("range")(_stub_check)

    assert get_check("range") is _stub_check
