# DataForge

A CLI tool that ingests vehicle measurement data (ASAM MDF / `.mf4` files), validates it
against configurable rules, and produces a pass/fail report.

DataForge is built as a batch job: it reads a measurement file and a rules file, runs each
configured check against the matching channel, writes a JSON report, and exits with a status
code reflecting the verdict. That last part is what makes it usable as a CI gate — a failed
check exits non-zero.

```bash
uv run dataforge \
  --measurement-file examples/demo.mf4 \
  --rules examples/demo_rules.yaml
```

## Where to start

- **{doc}`usage`** — running the CLI, the rules file format, exit codes.
- **{doc}`architecture`** — how ingestion, validation and reporting fit together, and how to
  add a new check or support a new file format.
- **{doc}`api/index`** — generated reference for every public module.

```{toctree}
:maxdepth: 2
:hidden:

usage
architecture
api/index
```
