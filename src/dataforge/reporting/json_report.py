import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from dataforge.reporting.base import Reporter
from dataforge.structs.result import AnalysisResult

logger = logging.getLogger(__name__)


class JSONReporter(Reporter):
    """Writes a `summary.json` containing check results."""

    def generate(self, result: AnalysisResult):
        """Generate the analysis report.

        Args:
            result: The `AnalysisResult` to be reported.
        """
        source_name = Path(result.source_file).stem
        run_name = f"{source_name}_{datetime.now(tz=UTC):%Y%m%d_%H%M%SZ}"
        run_dir = Path("output") / run_name
        run_dir.mkdir(parents=True, exist_ok=True)
        report_path = run_dir / "summary.json"
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
