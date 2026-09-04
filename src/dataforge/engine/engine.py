import logging
from pathlib import Path

from dataforge.enums.result import Result
from dataforge.ingestion import get_ingestor_for
from dataforge.structs.result import AnalysisResult
from dataforge.structs.signal import SignalSet
from dataforge.validation import get_check
from dataforge.validation import load_rules_from_yaml
from dataforge.reporting import JSONReporter

logger = logging.getLogger(__name__)


def run(measurement_file: Path, rules_yaml: Path) -> Result:
    """Run configured checks against a measurement file.
    
    Args:
        measurement_file: Path to the measurement file to be validated.
        rules_yaml: Path to the YAML file containing validation rules.
    
    Returns:
        Result.PASS if all checks pass, Result.FAIL if any check fails.
    """
    logger.info(f"Starting analysis of '{measurement_file}' using rules '{rules_yaml}'.")

    # VALIDATION RULES
    rules = load_rules_from_yaml(rules_yaml)

    # INGESTION
    ingestor = get_ingestor_for(measurement_file)
    logger.debug(f"Using ingestor {type(ingestor).__name__} for '{measurement_file}'.")
    signals: SignalSet = ingestor.load(measurement_file)

    # VALIDATION
    check_results = []
    for rule in rules:
        check_fn = get_check(rule["type"])
        logger.debug(f"Running check '{rule["type"]}' on channel '{rule["channel"]}'.")
        check_result = check_fn(
            channel=rule["channel"],
            signals=signals,
            **rule["parameters"],
        )
        logger.debug(
            f"Check '{rule["type"]}' on channel '{rule["channel"]}': {"PASSED" if check_result.passed else "FAILED"} - {check_result.message}"
        )
        check_results.append(check_result)

    analysis_result = AnalysisResult(
                source_file=measurement_file,
                check_results=check_results,
                rules_yaml=rules_yaml
            )

    # REPORTING
    reporter = JSONReporter()
    reporter.generate(analysis_result)

    failed = [check for check in check_results if not check.passed]
    if failed:
        logger.info(f"Analysis FAILED: {len(failed)} of {len(check_results)} checks failed.")
        for check in failed:
            logger.info(f"  {check.check_name} on {check.signal_name}: {check.message}")
        return Result.FAIL
    else:
        logger.info(f"Analysis PASSED: all {len(check_results)} check(s) passed.")
        return Result.PASS

    
