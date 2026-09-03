import json
from datetime import datetime
from pathlib import Path

from dataforge.reporting.base import Reporter
from dataforge.structs.result import AnalysisResult


class JSONReporter(Reporter):
    """Writes a `summary.json` containing check results."""
    def generate(self, result: AnalysisResult) -> Path:
        """Generate the analysis report.

        Args:
            result: The `AnalysisResult` to be reported.

        Returns:
            The path to the generated report file.
        """
        source_name = Path(result.source_file).stem
        run_name = f"{source_name}_{datetime.now():%Y%m%d_%H%M%S}"
        run_dir = Path("output") / run_name
        run_dir.mkdir(parents=True, exist_ok=True)
        report_path = run_dir / "summary.json"

        payload = {
            "source_file": result.source_file,
            "passed": result.passed,
            "check_results": [check.to_dict() for check in result.check_results],
        }
        with report_path.open("w") as file:
            json.dump(payload, file, indent=4)
        return report_path