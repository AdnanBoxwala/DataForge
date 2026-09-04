"""Unit tests for `dataforge.validation.rules`."""

import pytest
import yaml

from dataforge.validation.rules import load_rules_from_yaml


@pytest.mark.parametrize(
    "count",
    [
        pytest.param(0, id="no-rules"),
        pytest.param(1, id="one-rule"),
        pytest.param(3, id="several-rules"),
    ],
)
def test_loads_every_rule(make_rules_yaml, range_rule, count):
    path = make_rules_yaml([range_rule(channel=f"ch{i}") for i in range(count)])

    assert len(load_rules_from_yaml(path)) == count


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        pytest.param("type", "range", id="type"),
        pytest.param("channel", "speed", id="channel"),
        pytest.param("parameters", {"min_value": 0, "max_value": 232}, id="parameters"),
    ],
)
def test_preserves_rule_fields(make_rules_yaml, range_rule, key, expected):
    path = make_rules_yaml([range_rule(channel="speed", min_value=0, max_value=232)])

    assert load_rules_from_yaml(path)[0][key] == expected


def test_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="does not exist"):
        load_rules_from_yaml(tmp_path / "absent.yaml")


@pytest.mark.parametrize(
    "content",
    [
        pytest.param("checks: [unclosed\n", id="unclosed-bracket"),
        pytest.param("checks: {unclosed\n", id="unclosed-brace"),
        pytest.param("*undefined_alias\n", id="undefined-alias"),
        pytest.param('checks: "unterminated\n', id="unterminated-string"),
    ],
)
def test_malformed_yaml_raises_value_error(tmp_path, content):
    path = tmp_path / "broken.yaml"
    path.write_text(content)

    with pytest.raises(ValueError, match="Error parsing YAML file"):
        load_rules_from_yaml(path)


def test_malformed_yaml_preserves_the_original_cause(tmp_path):
    """The re-raise uses `from e`, so the YAML error stays in the chain."""
    path = tmp_path / "broken.yaml"
    path.write_text("checks: [unclosed\n")

    with pytest.raises(ValueError) as exc_info:
        load_rules_from_yaml(path)

    assert isinstance(exc_info.value.__cause__, yaml.YAMLError)
