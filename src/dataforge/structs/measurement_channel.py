from dataclasses import dataclass
from typing import Optional

@dataclass
class MeasurementChannel:
    """
    A data structure representing a signal with its properties.
    """
    name: str
    samples: list
    timestamps: list
    unit: Optional[str]
    