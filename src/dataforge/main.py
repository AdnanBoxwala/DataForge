from pathlib import Path

from dataforge.engine import run


def main() -> None:
    measurement_file = Path("./data/sample/sample_speed.mf4")
    rules_yaml = Path("./data/rules.yaml")

    run(measurement_file, rules_yaml)

if __name__ == "__main__":
    main()