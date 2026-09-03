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
uv run dataforge <measurement_file.mf4> <rules.yaml>
```

Example, using the sample fixture and rules bundled in the repo:
```bash
uv run dataforge data/sample/sample_speed.mf4 data/rules.yaml
```

This ingests the `.mf4` file, runs each check defined in the rules YAML against the matching channel, and writes a JSON report. The path to the generated report is printed on completion.

### Rules format

Rules are defined in a YAML file, e.g. [`data/rules.yaml`](data/rules.yaml):
```yaml
checks:
  - type: range
    channel: speed
    parameters:
      min_value: 0
      max_value: 232
```

## Project structure

```
src/dataforge/
├── ingestion/       # MDF loading (asammdf)
├── validation/      # rule loading + checks (range, dropout, stale-signal, ...)
├── engine/          # wires ingestion -> validation -> reporting together
├── reporting/       # report generation (JSON)
├── structs/         # shared data types (SignalSet, AnalysisResult, ...)
└── main.py          # CLI entry point
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

Run tests:
```bash
uv run pytest
```
