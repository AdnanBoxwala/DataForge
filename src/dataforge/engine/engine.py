from pathlib import Path

from dataforge.ingestion import get_ingestor_for
from dataforge.structs.result import AnalysisResult
from dataforge.structs.signal import SignalSet
from dataforge.validation import get_check
from dataforge.validation import load_rules_from_yaml
from dataforge.reporting import JSONReporter

def run(measurement_file: Path, rules_yaml: Path) -> Path:
    """Run configured checks against an ingested signal set."""
    # INGESTION
    ingestor = get_ingestor_for(measurement_file)
    signals: SignalSet = ingestor.load(measurement_file)

    # VALIDATION
    rules = load_rules_from_yaml(rules_yaml)
    check_results = []
    for rule in rules:
        check_fn = get_check(rule["type"])
        check_results.append(
            check_fn(
                channel=rule["channel"],
                signals=signals,
                **rule["parameters"],
            )
        )

    result = AnalysisResult(
                source_file=measurement_file,
                check_results=check_results,
                rules_yaml=rules_yaml
            )

    # REPORTING
    reporter = JSONReporter()
    return reporter.generate(result)