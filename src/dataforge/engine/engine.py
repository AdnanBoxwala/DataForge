import logging
from pathlib import Path

from dataforge.enums.result import Result
from dataforge.ingestion import get_ingestor_for
from dataforge.reporting import JSONReporter, archive_inputs, create_run_directory
from dataforge.structs.result import AnalysisResult
from dataforge.structs.signal import SignalSet
from dataforge.validation import get_check, load_rules_from_yaml

logger = logging.getLogger(__name__)


def run(
    measurement_file: Path, rules_yaml: Path, run_dir: Path | None = None
) -> Result:
    """Run configured checks against a measurement file.

    Args:
        measurement_file: Path to the measurement file to be validated.
        rules_yaml: Path to the YAML file containing validation rules.
        run_dir: Directory to write this run's artefacts into. When omitted a
            fresh one is created. The CLI passes its own so that the log file
            for the run can be opened before the analysis starts.

    Returns:
        Result.PASS if all checks pass, Result.FAIL if any check fails.
    """
    if run_dir is None:
        run_dir = create_run_directory(measurement_file)

    logger.info(
        f"Starting analysis of '{measurement_file}' using rules '{rules_yaml}'."
    )

    # Copy the inputs alongside the report before anything can fail, so a failed
    # run still records what it was given.
    archive_inputs(run_dir, measurement_file, rules_yaml)

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
        logger.debug(f"Running check '{rule['type']}' on channel '{rule['channel']}'.")
        check_result = check_fn(
            channel=rule["channel"],
            signals=signals,
            **rule["parameters"],
        )
        logger.debug(
            f"Check '{rule['type']}' on channel '{rule['channel']}': {'PASSED' if check_result.passed else 'FAILED'} - {check_result.message}"
        )
        check_results.append(check_result)

    analysis_result = AnalysisResult(
        source_file=measurement_file, check_results=check_results, rules_yaml=rules_yaml
    )

    # REPORTING
    reporter = JSONReporter(run_dir)
    reporter.generate(analysis_result)

    failed = [check for check in check_results if not check.passed]
    if failed:
        logger.info(
            f"Analysis FAILED: {len(failed)} of {len(check_results)} checks failed."
        )
        for check in failed:
            logger.info(f"  {check.check_name} on {check.signal_name}: {check.message}")
        return Result.FAIL
    else:
        logger.info(f"Analysis PASSED: all {len(check_results)} check(s) passed.")
        return Result.PASS
