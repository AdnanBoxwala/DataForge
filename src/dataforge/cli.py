import argparse
import logging
import sys
from pathlib import Path

from dataforge.engine import run
from dataforge.enums.result import Result
from dataforge.logging import configure_logging

logger = logging.getLogger(__name__)


def main() -> Result:
    parser = argparse.ArgumentParser(description="Validate an MDF measurement file.")
    parser.add_argument(
        "--measurement-file", "-f",
        type=Path,
        required=True,
        help="Path to the .mf4 file.",
    )
    parser.add_argument(
        "--rules", "-r",
        type=Path,
        required=True,
        help="Path to the validation rules YAML file.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )
    parser.add_argument(
        "--log-file", "-log",
        type=Path,
        default=None,
        help="Additionally write log output to this file.",
    )
    args = parser.parse_args()

    configure_logging(verbose=args.verbose, log_file=args.log_file)
    logger.debug(f"Parsed arguments: measurement_file='{args.measurement_file}' rules='{args.rules}' verbose={args.verbose} log_file='{args.log_file}'")

    try:
        result = run(args.measurement_file, args.rules)
    except (FileNotFoundError, ValueError, KeyError) as e:
        logger.error(e)
        sys.exit(1)
    except Exception:
        logger.exception("Unexpected error during analysis.")
        sys.exit(1)

    if result is Result.FAIL:
        sys.exit(1)
    sys.exit(0)



if __name__ == "__main__":
    main()