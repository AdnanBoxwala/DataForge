from abc import ABC, abstractmethod
from pathlib import Path

from dataforge.structs.result import AnalysisResult


class Reporter(ABC):
    """Abstract base class for reporting analysis results."""

    @abstractmethod
    def generate(self, result: AnalysisResult) -> Path:
        """Generate the analysis report.

        Args:
            result: The `AnalysisResult` to be reported.

        Returns:
            The path to the generated report file.
        """
        pass