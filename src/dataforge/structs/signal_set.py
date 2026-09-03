from dataclasses import dataclass
from pathlib import Path

from dataforge.structs.measurement_signal import MeasurementSignal


@dataclass
class SignalSet:
    """A collection of signals loaded from a single measurement file.

    Attributes:
        signals (dict[str, MeasurementSignal]): Mapping of signal name to `MeasurementSignal`.
        source (Path): The path to the originating measurement file.
    """
    signals: dict[str, MeasurementSignal]
    source: Path

    def get(self, name: str) -> MeasurementSignal:
        """Return a signal by name, raising a clear error if it doesn't exist.

        Args:
            name: Signal name to look up.

        Returns:
            The corresponding `MeasurementSignal` object.

        Raises:
            KeyError: If the signal with the given name does not exist in the set.
        """
        return self.signals[name]