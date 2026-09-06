# Architecture

DataForge is deliberately small. The application exists to be validated, containerised and
deployed, so the code favours clear seams over features.

## The pipeline

A run is a straight line through four stages:

```
rules.yaml ──► load_rules_from_yaml ─┐
                                     ├─► run() ──► JSONReporter ──► summary.json
measurement.mf4 ──► MDFIngestor ─────┘
```

1. **Rules are loaded first.** This is deliberate: parsing a small YAML file is cheap, so a
   typo in the rules path fails immediately rather than after a large measurement file has
   been parsed.
2. **Ingestion** resolves an ingestor from the file extension and converts the file into a
   `SignalSet` — a plain mapping of channel name to `MeasurementSignal`.
3. **Validation** looks up each rule's check function by name and calls it against the
   `SignalSet`, collecting a `CheckResult` per rule.
4. **Reporting** serialises the collected results.

`run()` returns `Result.PASS` or `Result.FAIL`, and the CLI turns that into the process exit
code.

## Why the seams are where they are

**Ingestion is an adapter.** `asammdf` has its own `Signal` class, and nothing outside
`dataforge.ingestion` refers to it. Channels are converted into `MeasurementSignal` at the
boundary, so the validation and reporting layers have no knowledge of MDF at all. A CSV or
Parquet ingestor could be added without touching them.

**Checks and ingestors are found by registry, not by branching.** Both use a decorator that
records the implementation in a module-level dict:

```python
@register_check("range")
def range_check(channel, signals, min_value, max_value): ...
```

Adding a check means adding a function, not editing a dispatch table. The cost is an import
side effect: the module defining the check has to be imported for the registration to run,
which is why `dataforge/validation/__init__.py` imports `range_check` and re-exports it
through `__all__`. Removing that seemingly unused import empties the registry.

**Numpy arrays are the shared currency.** `MeasurementSignal.samples` and `.timestamps` are
`NDArray`, not lists. Measurement files run to millions of samples, and every plausible
ingestor (`asammdf`, pandas, pyarrow) produces numpy natively, so converting would cost both
performance and dtype information.

## Adding a check

1. Write a function taking `channel: str`, `signals: SignalSet`, and whatever parameters the
   check needs as keyword arguments; return a `CheckResult`.
2. Decorate it with `@register_check("your_name")`.
3. Import it in `dataforge/validation/__init__.py` and add it to `__all__`, so the
   registration runs and linters do not strip the import.
4. Reference it from a rules file by the name you registered.

```python
from dataforge.structs.result import CheckResult
from dataforge.structs.signal import SignalSet
from dataforge.validation.base import register_check


@register_check("not_empty")
def not_empty_check(channel: str, signals: SignalSet) -> CheckResult:
    """Fail if a channel contains no samples."""
    signal = signals.get(channel)
    passed = len(signal.samples) > 0
    return CheckResult(
        check_name="not_empty",
        signal_name=channel,
        parameters={},
        passed=passed,
        message=f"Signal '{channel}' has {len(signal.samples)} sample(s).",
    )
```

## Adding an ingestor

Subclass `Ingestor`, set `file_extension`, implement `load()`, and decorate with
`@register_ingestor`. The same import-side-effect rule applies.

The contract `load()` must honour: raise `FileNotFoundError` if the path does not exist, and
return a `SignalSet` whose signals carry numpy arrays. Note that the current MDF ingestor
lets `asammdf`'s own `MdfException` propagate on a corrupt file rather than translating it,
which leaks the library through the adapter boundary.

## Testing layers

| Suite | What it covers | Speed |
|---|---|---|
| `tests/unit` | Individual functions and classes, fully isolated | ~0.4s |
| `tests/integration` | The installed console script in a subprocess — entry point, exit codes, stdout/stderr split | seconds |
| `tests/regression` | Whole-pipeline output against a committed baseline | seconds |

The regression fixture carries deliberate faults — an out-of-range spike, a frozen signal, a
gap in the timebase — so the baseline records both what is caught and what currently is not.
A frozen signal passing is a recorded fact, not an oversight: when a stale-signal check is
added, that test fails and prompts a reviewed baseline update.
