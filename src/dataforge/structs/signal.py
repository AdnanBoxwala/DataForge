from dataclasses import dataclass
from numpy.typing import NDArray
from pathlib import Path
from typing import Optional


@dataclass
class MeasurementSignal:
    """A single time-series channel, decoupled from any specific file format.

    Attributes:
        name: Signal name, e.g. "vehicle-speed".
        samples: 1D array of sample values. Must be the same length as timestamps.
        timestamps: 1D array of sample times, in seconds.
        unit: Physical unit, e.g. "km/h".
    """
    name: str
    samples: NDArray
    timestamps: NDArray
    unit: Optional[str]


@dataclass
class SignalSet:
    """A collection of signals loaded from a single measurement file.

    Attributes:
        signals: Mapping of signal name to `MeasurementSignal`.
        source: The path to the originating measurement file.
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
        try:
            return self.signals[name]
        except KeyError:
            raise KeyError(f"Signal '{name}' not found in the provided SignalSet.")