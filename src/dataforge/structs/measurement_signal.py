from dataclasses import dataclass
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
    