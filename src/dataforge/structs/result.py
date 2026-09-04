from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    """Represents the result of a check.

    Attributes:
        check_name: The name of the check performed.
        signal_name: The name of the signal that was checked.
        parameters: A dictionary of parameters used for the check.
        passed: Whether the check passed or failed.
        message: An optional message providing additional information about the check result.
    """

    check_name: str
    signal_name: str
    parameters: dict
    passed: bool
    message: str

    def to_dict(self) -> dict:
        """Convert the CheckResult to a dictionary representation.

        Returns:
            A dictionary containing the check result information.
        """
        return {
            "check_name": self.check_name,
            "signal_name": self.signal_name,
            "parameters": self.parameters,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass
class AnalysisResult:
    """Represents the result of an analysis.

    Attributes:
        source_file: The path to the source file that was analyzed.
        check_results: A list of `CheckResult` objects representing the results of individual checks.
        rules_yaml: The path to the YAML file containing the rules used for the analysis.
    """

    source_file: Path
    check_results: list[CheckResult]
    rules_yaml: Path

    @property
    def passed(self) -> bool:
        """Determine if all checks passed.

        Returns:
            True if all checks passed, False otherwise.
        """
        return all(result.passed for result in self.check_results)
