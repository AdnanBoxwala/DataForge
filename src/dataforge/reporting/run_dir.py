"""Layout of a single run's output directory.

Every run writes its artefacts into ``output/<measurement-name>_<timestamp>/``::

    output/demo_20260906_080442Z/
    ├── summary.json      the report
    ├── dataforge.log     the log for this run
    └── inputs/           copies of the measurement and rules files

The directory is created before the analysis starts rather than by the reporter
at the end, because the log file has to be opened before there is anything to
report. A run that fails therefore still leaves a directory behind, containing
the log that explains why - which is usually what you want from a CI artefact.
"""

import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

#: Log file name used when the caller does not supply one.
DEFAULT_LOG_NAME = "dataforge.log"

#: Subdirectory holding copies of the run's inputs.
INPUTS_DIR_NAME = "inputs"


def create_run_directory(
    measurement_file: Path, base_dir: Path = Path("output")
) -> Path:
    """Create the output directory for a single run.

    The name combines the measurement file's stem with a UTC timestamp, so
    repeated runs over the same file do not overwrite each other.

    Args:
        measurement_file: The measurement being analysed. Only its name is used,
            so it does not need to exist yet.
        base_dir: Directory the run directory is created inside, relative to the
            current working directory unless absolute.

    Returns:
        The created run directory.
    """
    run_name = f"{measurement_file.stem}_{datetime.now(tz=UTC):%Y%m%d_%H%M%SZ}"
    base_dir.mkdir(parents=True, exist_ok=True)

    # The timestamp has second resolution, so two runs over the same file within
    # one second would otherwise share a directory - the second overwriting the
    # first's report and inputs, and both logs ending up side by side. Claim the
    # directory exclusively and disambiguate rather than merging into it.
    run_dir = base_dir / run_name
    suffix = 1
    while True:
        try:
            run_dir.mkdir()
            break
        except FileExistsError:
            suffix += 1
            run_dir = base_dir / f"{run_name}_{suffix}"

    logger.debug(f"Created run directory '{run_dir}'.")
    return run_dir


def archive_inputs(run_dir: Path, *inputs: Path) -> list[Path]:
    """Copy the run's input files into ``<run_dir>/inputs/``.

    Keeping a copy alongside the report means a run can be reproduced later even
    if the originals move or change. Inputs that do not exist are skipped rather
    than raising, so the caller still gets the clearer error from whichever
    component actually needed the file.

    Args:
        run_dir: The run directory to copy into.
        *inputs: Files to copy.

    Returns:
        The paths of the copies that were made, in the order given.
    """
    inputs_dir = run_dir / INPUTS_DIR_NAME
    inputs_dir.mkdir(parents=True, exist_ok=True)

    archived: list[Path] = []
    for source in inputs:
        if not source.is_file():
            logger.debug(f"Not archiving '{source}': it does not exist.")
            continue
        destination = inputs_dir / source.name
        shutil.copy2(source, destination)
        archived.append(destination)
        logger.debug(f"Archived '{source}' to '{destination}'.")

    if archived:
        logger.info(f"Archived {len(archived)} input file(s) to '{inputs_dir}'.")
    return archived
