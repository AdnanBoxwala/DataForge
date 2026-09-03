from __future__ import annotations

from collections.abc import Callable

from dataforge.structs.result import CheckResult

Checkfunc = Callable[..., CheckResult]
_CHECK_REGISTRY: dict[str, Checkfunc] = {}


def register_check(name: str) -> Callable[[Checkfunc], Checkfunc]:
    """Decorator to register a check function.

    Args:
        name: The name of the check.

    Returns:
        A decorator that registers the check function.
    """
    def decorator(func: Checkfunc) -> Checkfunc:
        _CHECK_REGISTRY[name] = func
        return func
    return decorator


def get_check(name: str) -> Checkfunc:
    """Get a registered check function by name.

    Args:
        name: The name of the check.

    Returns:
        The registered check function.

    Raises:
        KeyError: If the check is not registered.
    """
    if name not in _CHECK_REGISTRY:
        raise KeyError(
            f"Check '{name}' is not registered. "
            f"Available checks: {sorted(_CHECK_REGISTRY.keys())}"
        )
    return _CHECK_REGISTRY[name]