from abc import ABC, abstractmethod

from dataforge.structs.result import AnalysisResult


class Reporter(ABC):
    """Abstract base class for reporting analysis results."""

    @abstractmethod
    def generate(self, result: AnalysisResult):
        """Generate the analysis report.

        Args:
            result: The `AnalysisResult` to be reported.
        """
