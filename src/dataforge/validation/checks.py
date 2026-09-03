from dataforge.structs.signal import SignalSet
from dataforge.structs.result import CheckResult
from dataforge.validation.base import register_check


@register_check("range")
def range_check(name: str, signals: SignalSet, min_value: float, max_value: float) -> CheckResult:
    """Check if the values of a signal are within a specified range.

    Args:
        name: The name of the signal to check.
        signals: The SignalSet containing the signal.
        min_value: The minimum acceptable value, inclusive.
        max_value: The maximum acceptable value, inclusive.

    Returns:
        A `CheckResult` indicating whether all values are within the range.
    """
    try:
        signal = signals.get(name)
    except KeyError:
        raise ValueError(f"Signal '{name}' not found in the provided SignalSet.")
    
    passed = True
    message = f"Signal '{name}' is within the specified range."
    for index, value in enumerate(signal.samples):
        if not min_value <= value <= max_value:
            passed = False
            timestamp = signal.timestamps[index]
            message = (
                f"Signal '{name}' has value {value} at timestamp {timestamp}, "
                f"which is outside the specified range."
            )
            break

    return CheckResult(
        check_name="range",
        signal_name=name,
        passed=passed,
        message=message)