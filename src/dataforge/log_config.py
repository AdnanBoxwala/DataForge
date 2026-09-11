import logging
import sys
from pathlib import Path


def configure_logging(
    verbose: bool = False,
    log_file: Path | None = None,
) -> None:
    """Configure root logging for the application.

    Args:
        verbose: If True, emit DEBUG-level messages; otherwise INFO and above.
        log_file: Optional path to additionally write log output to.
    """
    level = logging.DEBUG if verbose else logging.INFO

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stderr),
    ]

    if log_file is not None:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )
