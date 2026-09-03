# DataForge — Project Context

## What this is

DataForge is a Python CLI tool that ingests vehicle measurement data (ASAM MDF / `.mf4` files), validates it against a configurable, pluggable set of rules, computes summary KPIs, and produces a pass/fail report (JSON + HTML + plots).

This project is the applied side of a 9-day self-directed DevOps training plan. The application itself is intentionally small — it exists to give real CI/CD, containerization, and cloud-deployment work something concrete to build around. Don't over-build the application logic; the infrastructure and tooling around it is the actual point.

## Goals

- Build a genuinely working, testable, containerized Python tool — not a toy demo.
- Use it as the vehicle for hands-on DevOps practice: CI/CD, Docker, AWS, Terraform, Kubernetes, security scanning, observability.
- End with a portfolio-quality repository: clean architecture, real tests, documented decisions, a working cloud deployment.
- Keep the tool's *architecture* domain-agnostic even though the initial data adapter is automotive-specific (MDF). The validation engine, rule format, and reporting layer should not assume MDF is the only possible input — a CSV/Parquet adapter should be able to sit alongside it without touching the rest of the code.

## Domain & data model

- Input: `.mf4` files via the `asammdf` library.
- `asammdf` has its own class called `Signal` — the internal data class in this project uses a different name (e.g. `MeasurementSignal` or `ChannelData`) to avoid import/naming collisions.
- Two categories of `.mf4` files exist in this repo, and they must not be conflated:
  1. **Regression fixtures** (`data/sample/`) — small, synthetic, generated with known fault injections. CI tests assert specific expected outcomes against these. These are what `pytest` uses.
  2. **Production-like scenario file(s)** (`data/production-like/`) — larger, synthetic, more realistic, deliberately *not* asserted against in any test. This is the file the AWS deployment actually processes. Its purpose is to demonstrate the tool being *used* on unseen data, not to re-prove correctness CI already proved. Never point the AWS/ECS run at a regression fixture — that would make the cloud deployment redundant with CI.
- A synthetic data generator (with deliberate fault injection: out-of-range spikes, dropped samples, stale/frozen stretches) produces both categories of files. Real downloaded MDF samples (e.g. from CSS Electronics) are an optional future enhancement, not part of the current scope — they require DBC decoding (`cantools`) which isn't in scope yet.

## Architecture

```
dataforge/
├── src/dataforge/
│   ├── enums/
│   ├── ingestion/       # MDF loader (asammdf) — designed so CSV/Parquet adapters could be added later
│   ├── validation/      # Check base class (ABC) + built-in checks (range, dropout, stale-signal)
│   ├── processing/      # signal transforms, KPI computation
│   ├── reporting/       # JSON/HTML/plot output
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── regression/      # asserts against data/sample/ fixtures with known baselines
├── data/
│   ├── sample/               # small CI regression fixtures
│   └── production-like/      # larger, unasserted "new data" file(s) — used by the AWS run
├── docs/                 # Sphinx source; published to GitHub Pages via CI
├── terraform/
├── .github/workflows/
├── Jenkinsfile
└── pyproject.toml
```

Validation checks are built against a `Check` abstract base class with a `run(signal_set) -> CheckResult` method, loaded/configured via a `rules.yaml` file. New checks should be added as new `Check` subclasses, not by branching inside existing ones.

## Tech stack & key decisions (don't second-guess these without reason)

| Choice | Not this | Why |
|---|---|---|
| CLI application | FastAPI / web service | The tool is a batch job; a service would exist only to justify infrastructure, not because the app needs it |
| `uv` for env/deps | `pip` + `venv` directly | Always work inside a virtual environment (`uv venv` / `uv run`), never against system Python |
| ECS/Fargate for cloud deploy | EKS | Same underlying value (containers running in AWS) without the OIDC-to-cluster-auth overhead; Kubernetes is learned separately, locally |
| Kubernetes via local `kind` cluster | EKS | Purely a learning exercise in Kubernetes concepts — this never gets deployed to AWS, and has no dependency on the ECS path |
| GitHub Actions as primary CI | — | Also mirrored in a second, parallel Jenkins pipeline running the same stages, for direct platform comparison |
| GHCR *and* ECR | Just one registry | Image is built and scanned once, then pushed to both — never rebuilt or rescanned for the second registry |
| Sphinx + autodoc | Doxygen | Doxygen is native to C/C++; Sphinx is Python's own standard tooling and reads docstrings directly |
| Terraform | Manual console / CloudFormation | Infrastructure as code, with remote state (S3 backend) and CI-integrated `plan` review |

## Pipeline sequencing (important — don't reorder this logic in CI configs)

Tests must gate the build, and the scan must gate the push. The correct order is:

```
push/merge → run tests → (only if tests pass) build image → scan image
    → (only if scan passes) push to GHCR → re-tag & push same image to ECR
    → run on ECS/Fargate
```

Never push an image before it's scanned. Never rebuild or rescan an image between registries — the same artifact that passed Trivy is what goes everywhere.

## Development conventions

- Trunk-based development, Conventional Commits, semantic versioning.
- `ruff` for lint/format, `mypy` for type checking, `pytest` for tests (unit + integration + regression baseline).
- Docstrings on public classes/functions (Google or NumPy style) — these feed the auto-published Sphinx docs.
- Regression tests compare actual output against a committed baseline JSON — if a change breaks the baseline, either the change is wrong or the baseline needs a deliberate, reviewed update. Never silently update a baseline to make a test pass.

## Out of scope for now (don't build unprompted)

- FastAPI or any always-on service.
- Kubernetes on AWS (EKS).
- Real CAN log ingestion / DBC decoding (`cantools`) — noted as a future enhancement only.
- Fully event-driven S3→Lambda→ECS triggering — current pipeline triggers the AWS run from CI on merge, not from a file-upload event. This is a documented "what's next," not a current requirement.
- Multi-environment (dev/staging/prod) Terraform setups.

## Current status

Track progress against the 9-day plan below. Ask before jumping ahead to a later day's infrastructure work if earlier foundations (tests passing, Docker image building cleanly) aren't done yet.

1. App scaffold, MDF generator (fixtures + production-like file), ingestion, basic checks, CLI
2. Type hints, tests, linting, Sphinx docstrings/local build, packaging
3. Dockerfile (multi-stage, non-root), Compose
4. GitHub Actions CI (test → build → scan → push GHCR), docs publishing to GitHub Pages
5. AWS fundamentals, IAM, OIDC setup
6. Terraform (VPC, ECR, ECS, S3), CI-triggered AWS deployment
7. Kubernetes locally (kind) — Job manifest, debugging practice
8. Trivy/SBOM, Grafana dashboard, incident postmortem, parallel Jenkins pipeline
9. Documentation, ADRs, cleanup