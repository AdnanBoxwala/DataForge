from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class MeasurementSignal:
    """A single time-series channel, decoupled from any specific file format.

    Attributes:
        name (str): Signal name, e.g. "vehicle-speed".
        samples (list): 1D array of sample values. Must be the same length as timestamps.
        timestamps (list): 1D array of sample times, in seconds.
        unit (Optional[str]): Physical unit, e.g. "km/h".
        source_file (Optional[str]): Path to the file this signal was loaded from, kept for traceability in reports and error messages.
    """
    name: str
    samples: list
    timestamps: list
    unit: Optional[str]
    source_file: Optional[str]


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