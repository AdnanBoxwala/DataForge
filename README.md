# DataForge

A CLI tool that ingests vehicle measurement data (ASAM MDF / `.mf4` files), validates it against configurable rules, and produces a pass/fail report.

## Setup

This project uses [`uv`](https://docs.astral.sh/uv/) for Python environment and dependency management.

### 1. Install uv

macOS/Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or via Homebrew:
```bash
brew install uv
```

### 2. Clone the repo

```bash
git clone <repo-url>
cd DataForge
```

### 3. Install dependencies

```bash
uv sync
```

This creates a `.venv` and installs everything pinned in `uv.lock`, using the Python version specified in `.python-version` (uv will download it automatically if it's not already installed).

## Usage

```bash
uv run dataforge --measurement-file <measurement_file> --rules <rules.yaml>
```

Example, using the demo files bundled in [`examples/`](examples/):
```bash
uv run dataforge \
  --measurement-file examples/demo.mf4 \
  --rules examples/demo_rules.yaml
```

That demo passes every check and exits `0`.

The `--measurement-file` argument accepts a path to a measurement file. DataForge selects an ingestor based on the file extension; currently, only the MDF `.mf4` ingestor is registered. Additional ingestors can be added without changing the CLI.

The tool runs each check defined in the rules YAML against the matching channel and writes a JSON report to `output/<measurement-name>_<timestamp>/summary.json`, relative to the current working directory.

Use `--verbose` or `-v` to enable DEBUG-level logging:

```bash
uv run dataforge \
  --measurement-file examples/demo.mf4 \
  --rules examples/demo_rules.yaml \
  --verbose
```

Use `--log-file` to additionally write log output to a file:

```bash
uv run dataforge \
  --measurement-file examples/demo.mf4 \
  --rules examples/demo_rules.yaml \
  --log-file output/dataforge.log
```

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Every check passed |
| `1` | A check failed, or the run errored (missing file, malformed rules, unsupported format) |
| `2` | Invalid command line arguments |

### Rules format

Rules are defined in a YAML file, e.g. [`examples/demo_rules.yaml`](examples/demo_rules.yaml):
```yaml
checks:
  - type: range
    channel: speed
    parameters:
      min_value: 0
      max_value: 232
```

Each entry names a registered check `type`, the `channel` to apply it to, and the `parameters` that check accepts.

## Project structure

```
src/dataforge/
├── ingestion/       # MDF loading (asammdf)
├── validation/      # rule loading + checks (range, dropout, stale-signal, ...)
├── engine/          # wires ingestion -> validation -> reporting together
├── reporting/       # report generation (JSON)
├── structs/         # shared data types (SignalSet, AnalysisResult, ...)
├── enums/           # shared enumerations (Result, ...)
├── logging.py       # logging configuration
└── cli.py           # CLI entry point
examples/            # small demo measurement + rules, shipped in the image
tests/
├── unit/            # fast, isolated
├── integration/     # drives the installed console script
└── regression/      # asserts pipeline output against a committed baseline
    ├── fixtures/    # small, frozen .mf4 + rules with injected faults
    └── baselines/   # expected reports
```

See [`PLAN.md`](PLAN.md) for full architecture and project context.

## Development

Add a new dependency:
```bash
uv add <package-name>
```

Add a dev-only dependency (e.g. test/lint tools):
```bash
uv add --dev <package-name>
```

### Tests

```bash
uv run pytest                                          # everything
uv run pytest -m "not integration and not regression"  # unit only, ~0.4s
uv run pytest -m integration                           # console-script end-to-end
uv run pytest -m regression                            # baseline comparison
```

Integration and regression tests spawn the installed `dataforge` executable in a subprocess, so they are noticeably slower than the unit suite.

### Regression baseline

`tests/regression/` compares the pipeline's output against a committed baseline at `tests/regression/baselines/regression_v1.json`. A failure means the report changed — either the change under review is wrong, or the baseline needs a deliberate, reviewed update:

```bash
uv run python tests/regression/generate_baseline.py
```

Never regenerate the baseline just to make a failing test pass. The fixture itself is frozen and is only rewritten with `--rebuild-fixture`, since the MDF header embeds a creation timestamp that changes its bytes on every write.
