import json
import logging
from pathlib import Path

from dataforge.reporting.base import Reporter
from dataforge.structs.result import AnalysisResult

logger = logging.getLogger(__name__)


class JSONReporter(Reporter):
    """Writes a `summary.json` into a run directory."""

    def __init__(self, run_dir: Path) -> None:
        """Create a reporter that writes into an existing run directory.

        The directory is supplied rather than derived here because the log file
        for the run is opened in it long before there is a report to write.

        Args:
            run_dir: Directory to write `summary.json` into.
        """
        self.run_dir = run_dir

    def generate(self, result: AnalysisResult) -> Path:
        """Generate the analysis report.

        Args:
            result: The `AnalysisResult` to be reported.

        Returns:
            The path to the generated report file.
        """
        self.run_dir.mkdir(parents=True, exist_ok=True)
        report_path = self.run_dir / "summary.json"
        logger.debug(f"Writing JSON report to '{report_path}'.")

        payload = {
            "source_file": str(result.source_file),
            "rules_yaml": str(result.rules_yaml),
            "passed": result.passed,
            "check_results": [check.to_dict() for check in result.check_results],
        }
        with report_path.open("w") as file:
            json.dump(payload, file, indent=4)
        logger.info(f"Report written to '{report_path}'.")
        return report_path
