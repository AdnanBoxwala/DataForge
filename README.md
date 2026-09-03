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

### 4. Run the CLI

```bash
uv run dataforge
```

`uv run` executes commands inside the project's virtual environment without needing to activate it manually.

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
