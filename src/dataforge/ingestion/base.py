from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from dataforge.structs.signal import SignalSet

_INGESTOR_REGISTRY: dict[str, type[Ingestor]] = {}


class Ingestor(ABC):
    """Abstract base class for data ingestors.
    """

    #: File extension that this ingestor can handle. For example, ".mf4".
    #: Subclasses should set this attribute to specify the file extension they support.
    file_extension: str

    @abstractmethod
    def load(self, path: Path) -> SignalSet:
        """Read a measurement file and return the data in a structured format.

        Args:
            path: Path to the measurement file.
        
        Returns:
            Structured data containing every channel found in the file.

        Raises:
            FileNotFoundError: If `path` does not exist.
            ValueError: If the file cannot be read or is in an unsupported format.
        """


def register_ingestor(ingestor_class: type[Ingestor]) -> type[Ingestor]:
    """Class decorator that registers an `Ingestor` subclass by its `file extension`.

    Usage:
        @register_ingestor
        class MyIngestor(Ingestor):
            file_extension = ".myext"
            ...

    Args:
        ingestor_class: The `Ingestor` subclass to register.

    Returns:
        The same class, unmodified, so this can be used as a decorator.
    """
    _INGESTOR_REGISTRY[ingestor_class.file_extension] = ingestor_class
    return ingestor_class


def get_ingestor_for(path: Path) -> Ingestor:
    """Return the registered `Ingestor` instance for a file's extension.

    Args:
        path (Path): Path to the measurement file.

    Returns:
        An instance of the `Ingestor` class registered for the given file extension.

    Raises:
        ValueError: If no ingestor is registered for the given file extension.
    """
    ingestor_class = _INGESTOR_REGISTRY.get(path.suffix)
    if ingestor_class is None:
        raise ValueError(
            f"No ingestor registered for file extension '{path.suffix}'. "
            f"Available extensions: {sorted(_INGESTOR_REGISTRY.keys())}"
        )
    return ingestor_class()