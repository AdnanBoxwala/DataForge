import logging
from pathlib import Path
import yaml

from dataforge.validation.base import CheckFunc, get_check

logger = logging.getLogger(__name__)


def load_rules_from_yaml(path: Path) -> list[dict]:
    """Load and parse a rules.yaml file into a list.

    Args:
        path: Path to the rules.yaml file.

    Returns:
        A list of dictionaries representing the parsed rules.

    Raises:
        FileNotFoundError: If `path` does not exist.
        ValueError: If the YAML is malformed, or references an unregistered
            check type.
    """
    logger.debug(f"Loading rules from '{path}'.")
    with open(path, "r") as file:
        try:
            rules = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}") from e

    checks = rules["checks"]
    logger.info(f"Loaded {len(checks)} rule(s) from '{path}'.")
    return checks