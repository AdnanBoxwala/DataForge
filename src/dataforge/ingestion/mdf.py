import logging
from pathlib import Path

from asammdf import MDF
from asammdf.blocks.utils import MdfException

from dataforge.ingestion.base import Ingestor, register_ingestor
from dataforge.structs.signal import MeasurementSignal, SignalSet

logger = logging.getLogger(__name__)


@register_ingestor
class MDFIngestor(Ingestor):
    """Ingestor for MDF (Measurement Data Format) files.

    This ingestor reads MDF files and extracts the measurement signals contained within.
    """

    file_extension = ".mf4"

    def load(self, path: Path) -> SignalSet:
        """Open an MDF file and extract all channels.

        Args:
            path: Path to the `.mf4` file.

        Returns:
            A `SignalSet` with every channel from the file.

        Raises:
            FileNotFoundError: If `path` does not exist.
        """
        if not path.exists():
            raise FileNotFoundError(f"The file '{path}' does not exist.")

        logger.debug(f"Opening MDF file '{path}'.")
        try:
            with MDF(path) as mdf:
                signals = {}
                for channel in mdf.iter_channels():
                    samples = channel.samples
                    timestamps = channel.timestamps
                    name = channel.name
                    unit = channel.unit

                    if name in signals:
                        logger.warning(
                            f"Duplicate channel name '{name}' in '{path}'; "
                            "the previously loaded channel will be overwritten."
                        )

                    signal = MeasurementSignal(
                        samples=samples, timestamps=timestamps, name=name, unit=unit
                    )
                    signals[name] = signal
                    logger.debug(
                        f"Ingested channel '{name}' ({len(samples)} samples, unit={unit})."
                    )

                logger.info(f"Loaded {len(signals)} channel(s) from '{path}'.")
                return SignalSet(signals=signals, source=path)
        except MdfException:
            raise ValueError(f"Could not load MDF file '{path}'.")
