# Release Notes — v1.3.0

**Released:** 2026-06-13
**Type:** Minor Feature Release — 5 new features, zero breaking changes

---

## Summary

v1.3.0 is a feature release focused on three goals: better observability across runs, broader hardware coverage, and richer framework integration — all without adding mandatory dependencies.

---

## New Features

### 1. Multi-Run History & Trends

Every `EcoTrace` session now carries a unique **Run ID** (a 12-character hex UUID fragment) and an optional **run label** set at construction time or via the CLI `--label` flag. Both values are written into every CSV row, allowing measurements to be grouped and compared across runs.

Two new CLI subcommands surface this data:

```bash
# Per-run summary table (newest first)
ecotrace history [-n 20]

# ASCII bar chart — visual carbon trend across last N runs
ecotrace trends [-n 10]
```

**Label a CI run:**
```bash
ecotrace run tests/test_core.py --label "pr-#142"
```

Existing CSV files without `RunID`/`RunLabel` columns are handled gracefully — DictReader returns empty strings for missing columns, which are displayed as `legacy`.

---

### 2. `get_summary()` Programmatic API

```python
eco = EcoTrace(region_code="TR")

@eco.track
def my_function():
    ...

my_function()

summary = eco.get_summary()
print(summary["total_carbon_gco2"])
print(summary["hardware"]["energy_sensor"])
print(summary["equivalence"])
```

Returns a fully structured dict with: `run_id`, `run_label`, `duration_s`, `functions_tracked`, `total_carbon_gco2`, `region`, `carbon_intensity`, `intensity_source`, `budget` (if configured), `equivalence`, and `hardware` metadata. No more parsing stdout or CSV to read session data programmatically.

---

### 3. Apple Silicon `powermetrics` Support

On Apple Silicon Macs (M1 / M2 / M3 / M4) where `sudo -n powermetrics` is accessible without a password prompt, EcoTrace now reads **exact hardware energy counters** instead of relying on Boavizta estimation.

```
Energy Sensor : Apple Silicon (powermetrics)
```

Falls back to Boavizta estimation silently on any failure — zero configuration required.

---

### 4. ML Framework Callbacks (`ecotrace.callbacks`)

Per-epoch carbon tracking for popular ML frameworks. **Neither PyTorch nor TensorFlow is a required dependency** — imports are deferred until the callback is instantiated.

**PyTorch (manual loop):**
```python
from ecotrace.callbacks.pytorch import EcoTracePyTorchCallback

cb = EcoTracePyTorchCallback(model_name="ResNet50")
cb.on_train_begin()
for epoch in range(num_epochs):
    cb.on_epoch_begin(epoch)
    train_one_epoch(model, dataloader, optimizer)
    val_loss = evaluate(model, val_loader)
    cb.on_epoch_end(epoch, metrics={"loss": val_loss})
cb.on_train_end()
```

**Keras / TensorFlow (`model.fit`):**
```python
from ecotrace.callbacks.keras import EcoTraceKerasCallback

model.fit(x_train, y_train, epochs=10,
          callbacks=[EcoTraceKerasCallback(model_name="BERT-base")])
```

Both callbacks log per-epoch carbon to the CSV audit log and print live per-epoch summaries.

**Optional install:**
```bash
pip install ecotrace[ml]    # PyTorch
pip install ecotrace[keras] # TensorFlow/Keras
```

---

### 5. Live Dashboard (`ecotrace dashboard`)

```bash
ecotrace dashboard [--port 8585] [--file ecotrace_log.csv]
```

Starts a **zero-dependency** (stdlib-only) localhost HTTP server and opens the dashboard in your browser automatically. Features:

- 🔴 Live carbon timeline chart (last 50 measurements)
- 📊 Per-function emissions bar chart (top 10)
- 🗂 Run history table with label badges
- 🔽 Run filter dropdown to isolate a specific session
- ♻️ Carbon equivalence display (Google searches, LED bulb minutes, etc.)
- ⟳ Auto-refreshes every 5 seconds via `fetch()`

No extra packages required — uses Python's built-in `http.server`, `json`, and `csv`, plus vanilla Canvas API for charts.

---

## Changes

- `_print_session_summary()` now delegates to `get_summary()` — eliminates duplicate logic.
- Session banner and exit summary both display the Run ID and label.
- `export_json()` `meta` block now includes `run_id` and `run_label`.
- `EcoTraceML.__exit__()` and ML CSV logging now propagate `RunID`/`RunLabel` from the internal `EcoTrace` instance.
- `ecotrace run --label` flag added to the CLI.

---

## Upgrade Notes

No breaking changes. Existing code and existing CSV files continue to work without modification.

New optional extras: `pip install ecotrace[ml]` and `pip install ecotrace[keras]`.
