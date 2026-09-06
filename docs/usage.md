# Usage

## Command line

```bash
uv run dataforge --measurement-file <measurement.mf4> --rules <rules.yaml>
```

Both arguments accept any path. DataForge has no data directory of its own — it reads the
files it is pointed at.

| Option | Short | Description |
|---|---|---|
| `--measurement-file` | `-f` | Path to the measurement file. Required. |
| `--rules` | `-r` | Path to the validation rules YAML. Required. |
| `--verbose` | `-v` | Emit DEBUG-level logging instead of INFO. |
| `--log-file` | `-log` | Additionally write log output to this file. |

Logs go to stderr; the report path goes to stdout. That separation means the report path can
be captured by a pipeline without log lines contaminating it.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Every check passed |
| `1` | A check failed, or the run errored (missing file, malformed rules, unsupported format) |
| `2` | Invalid command line arguments |

Note that `1` covers both "the data is bad" and "the run broke". A pipeline that needs to
distinguish them should read the report: if `summary.json` exists, the run completed and the
verdict is inside it.

## Output

A JSON report is written to `output/<measurement-name>_<timestamp>/summary.json`, relative to
the current working directory:

```json
{
    "source_file": "examples/demo.mf4",
    "rules_yaml": "examples/demo_rules.yaml",
    "passed": true,
    "check_results": [
        {
            "check_name": "range",
            "signal_name": "speed",
            "parameters": {"min_value": 0, "max_value": 232},
            "passed": true,
            "message": "Signal 'speed' is within the specified range."
        }
    ]
}
```

`passed` at the top level is the conjunction of every individual check — it is `true` only if
all of them passed. A rules file with no checks therefore reports `true`, since there was
nothing to violate.

## Rules format

Rules are a YAML document with a single `checks` key holding a list:

```yaml
checks:
  - type: range
    channel: speed
    parameters:
      min_value: 0
      max_value: 232
```

Each entry has three fields:

- **`type`** — the name of a registered check. Currently only `range` exists.
- **`channel`** — the signal in the measurement file to apply it to. Matched by exact name,
  case-sensitively.
- **`parameters`** — passed through as keyword arguments to the check function, so the
  accepted keys depend on the check.

Results appear in the report in the order the rules are listed.

### Available checks

#### `range`

Fails if any sample falls outside the given bounds, which are inclusive.

| Parameter | Description |
|---|---|
| `min_value` | Lowest acceptable value |
| `max_value` | Highest acceptable value |

The failure message names the **first** offending sample and its timestamp. Note that `NaN`
samples fail every comparison and are therefore reported as out of range, rather than as a
distinct "invalid sample" condition.

## Running in a container

The image contains the application only, so mount the files to analyse. `/work` is the
container's working directory, so mounting the project root there means inputs are read from
the mount and the report is written back into it:

```bash
docker build -t dataforge .
docker run --rm -v ".:/work" dataforge \
  -f /work/examples/demo.mf4 \
  -r /work/examples/demo_rules.yaml
```

Paths in the arguments are container paths, not host paths. Anything not mounted is invisible
to the container, and anything written outside a mount is lost when it exits.
