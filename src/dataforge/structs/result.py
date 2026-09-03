from dataclasses import dataclass


@dataclass
class CheckResult:
    """Represents the result of a check.

    Attributes:
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
        check_results: A list of `CheckResult` objects representing the results of individual checks.
    """

    source_file: str
    check_results: list[CheckResult]

    @property
    def passed(self) -> bool:
        """Determine if all checks passed.

        Returns:
            True if all checks passed, False otherwise.
        """
        return all(result.passed for result in self.check_results)