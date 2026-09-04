from pathlib import Path

from asammdf import MDF, Signal


def generate_sample_mdf(dest_path: Path, timestamps: list[float], channels: list[dict]) -> None:
    """Generate a sample MDF file with predefined signals.

    Args:
        dest_path: The path where the MDF file will be saved.
        timestamps: A list of timestamps for the signals.
        channels: A list of dictionaries, each containing 'samples', 'name', and 'unit' for a signal.
    """
    signals = []

    for channel in channels:
        signal = Signal(
            samples=channel["samples"],
            timestamps=timestamps,
            name=channel["name"],
            unit=channel["unit"]
        )
        signals.append(signal)

    # Create an empty MDF version 4.10 file
    with MDF(version='4.10') as mdf4:
        # Append the signal to the new file
        mdf4.append(signals, comment='sample mf4')

        # Save the new file
        mdf4.save(dest_path, overwrite=True)


generate_sample_mdf(
    dest_path=Path("./data/sample/sample_speed.mf4"),
    timestamps=[1,2,3,4,5,6,7,8,9,10],
    channels=[
        {
            "samples": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            "name": "speed",
            "unit": "kmph"
        }
    ]
)