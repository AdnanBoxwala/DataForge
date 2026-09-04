"""Regenerate the committed regression fixture and its baseline report.

    uv run python tests/regression/generate_baseline.py

This is deliberately NOT wired into pytest. A regression failure means either
the change under review is wrong, or the baseline needs a reviewed update - and
the diff this script produces is the thing a reviewer should read. Never run it
merely to make a failing test pass.

Run it when:
  * the fixture spec in `baseline_utils.py` is intentionally changed, or
  * a deliberate behaviour change alters the report, and the new output has been
    inspected and agreed.

The fixture is regenerated deterministically from the spec, so re-running with
an unchanged spec produces an identical `.mf4` payload and an identical baseline.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from baseline_utils import (
    BASELINE_JSON,
    FIXTURE_MDF,
    FIXTURE_RULES,
    normalise_report,
    write_fixture_mdf,
    write_fixture_rules,
)


def run_pipeline(measurement: Path, rules: Path, workdir: Path) -> dict:
    """Run the real CLI in `workdir` and return the report it wrote."""
    executable = Path(sys.executable).parent / "dataforge"
    if not executable.exists():
        raise SystemExit(
            f"dataforge console script not found at {executable}. Run 'uv sync' first."
        )

    process = subprocess.run(
        [str(executable), "-f", str(measurement), "-r", str(rules)],
        cwd=str(workdir),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,  # the exit code is what we assert on
    )
    print(process.stderr, end="", file=sys.stderr)

    reports = list(workdir.glob("output/*/summary.json"))
    if len(reports) != 1:
        raise SystemExit(f"expected exactly one report, found {reports}")
    return json.loads(reports[0].read_text())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild-fixture",
        action="store_true",
        help=(
            "Also rewrite the .mf4 and rules files. Off by default: asammdf "
            "stamps a creation time into the MDF header, so rewriting the "
            "fixture changes its bytes even when the data is identical."
        ),
    )
    args = parser.parse_args()

    if args.rebuild_fixture:
        print(f"Writing fixture   -> {FIXTURE_MDF}")
        write_fixture_mdf(FIXTURE_MDF)
        print(f"Writing rules     -> {FIXTURE_RULES}")
        write_fixture_rules(FIXTURE_RULES)
    else:
        print(f"Using fixture     -> {FIXTURE_MDF}")
        print(f"Using rules       -> {FIXTURE_RULES}")

    with tempfile.TemporaryDirectory() as tmp:
        payload = run_pipeline(FIXTURE_MDF, FIXTURE_RULES, Path(tmp))

    baseline = normalise_report(payload)
    BASELINE_JSON.parent.mkdir(parents=True, exist_ok=True)
    # indent=4 matches JSONReporter, so a baseline and a real report diff cleanly.
    BASELINE_JSON.write_text(json.dumps(baseline, indent=4) + "\n")
    print(f"Writing baseline  -> {BASELINE_JSON}")

    failed = [c for c in baseline["check_results"] if not c["passed"]]
    print(
        f"\nBaseline recorded: passed={baseline['passed']}, "
        f"{len(baseline['check_results'])} check(s), {len(failed)} failing."
    )
    print("Review the diff before committing.")


if __name__ == "__main__":
    main()
