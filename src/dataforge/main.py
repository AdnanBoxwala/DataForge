import argparse
from pathlib import Path

from dataforge.engine import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an MDF measurement file.")
    parser.add_argument("measurement_file", type=Path, help="Path to the .mf4 file.")
    parser.add_argument("rules_yaml", type=Path, help="Path to the validation rules YAML file.")
    args = parser.parse_args()

    report_path = run(args.measurement_file, args.rules_yaml)
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()