from asammdf import MDF
from pathlib import Path

from dataforge.ingestion.base import Ingestor, register_ingestor
from dataforge.structs.signal import MeasurementSignal, SignalSet


@register_ingestor
class MDFIngestor(Ingestor):
    """Ingestor for MDF (Measurement Data Format) files.

    This ingestor reads MDF files and extracts the measurement signals contained within.
    """

    file_extension = ".mf4"

    def load(self, path: Path) -> SignalSet:
        """Open an MDF file and convert every channel into a `SignalSet`.

        Args:
            path: Path to the `.mf4` file.

        Returns:
            A `SignalSet` with every channel from the file.

        Raises:
            FileNotFoundError: If `path` does not exist.
            ValueError: If the file is not a valid MDF file.
        """
        if not path.exists():
            raise FileNotFoundError(f"The file '{path}' does not exist.")
        with MDF(path) as mdf:
            signals = {}
            for channel in mdf.iter_channels():
                samples = channel.samples
                timestamps = channel.timestamps
                name = channel.name
                unit = channel.unit

                signal = MeasurementSignal(
                    samples=samples,
                    timestamps=timestamps,
                    name=name,
                    unit=unit,
                    source_file=str(path),
                )
                signals[name] = signal

            return SignalSet(signals=signals, source=path)
