# Release Notes — v1.4.0

**Released:** 2026-07-01
**Type:** Feature Release — 6 new features, 5 bug fixes, zero breaking changes

---

## Summary

v1.4.0 is a minor feature release introducing measurement pausing, webhook metrics exporting, side-by-side CLI run comparison (`ecotrace diff`), filtered CSV exporting, and log maintenance commands (`ecotrace clean` and `ecotrace reset`). It also fixes critical bug fixes related to ML callbacks, GPU monitor error handling, async source tracking, and CPU cache performance.

---

## New Features

### 1. Pausable Tracking API (`pause()` / `resume()`)

You can now pause and resume carbon tracking within an EcoTrace session to isolate your code's emissions from the overhead of setup, teardown, and data loaders.

```python
from ecotrace import EcoTrace

eco = EcoTrace(region_code="TR")

# Perform setup (unmeasured)
eco.pause()
expensive_setup_io()
eco.resume()

# Main processing block (measured)
@eco.track
def run_model():
    ...
```

The paused duration is automatically subtracted from the total session duration reported in `get_summary()`.

---

### 2. Side-by-Side Run Comparisons (`ecotrace diff`)

Compare any two tracking runs directly from the terminal to see if your code modifications reduced emissions.

```bash
# Compare two specific run IDs
ecotrace diff abc123def456 789012abc345

# Compare the latest two runs (CI/CD shortcut)
ecotrace diff --latest
```

Outputs a comparison of:
- Function call counts and delta
- Execution duration and delta
- Carbon emissions (gCO2) and delta (percentage and absolute)

---

### 3. Webhook Observability Exporter (`WebhookExporter`)

A new exporter allows you to stream carbon data to Webhooks in real-time. Ideal for Slack, MS Teams, Discord, or custom backend API integration.

```python
from ecotrace import EcoTrace
from ecotrace.exporters.webhook import WebhookExporter

eco = EcoTrace(region_code="TR")
WebhookExporter(eco, url="https://hooks.slack.com/services/...", headers={"Authorization": "Bearer token"})
```

---

### 4. Filtered CSV Exporting

We extended `ecotrace export` to output CSV files and filter output by Run ID/Label or Function Name.

```bash
# Export filtered CSV
ecotrace export --csv -o filtered_run.csv --run abc123def456
ecotrace export --csv -o test_funcs.csv --func "test_run"
```

---

### 5. Log Maintenance (`ecotrace clean` & `ecotrace reset`)

CLI utilities to manage log rotation and cleanup.

```bash
# Keep only the last 10 runs in ecotrace_log.csv (creates backup automatically)
ecotrace clean --keep-runs 10

# Delete entries before a specific date
ecotrace clean --before 2026-06-01

# Delete the log file entirely
ecotrace reset --yes
```

---

## Bug Fixes

- **ML Callbacks Carbon Calculation:** Removed duplicate and fragile carbon calculation formulas in Keras and PyTorch callbacks, delegating directly to `EcoTraceML.log_epoch()` which now returns the exact computed value.
- **Empty GPU monitoring crash:** Bypassed CSV log entries and PDF generation in `EcoTraceML` if `power_history` is empty.
- **Async Hotspots:** Added `file_path` and `line_number` source lookup in `measure_async()`, restoring hotspot tracking in async functions.
- **CPU caching performance:** Bypassed duplicate `cpuinfo.get_cpu_info()` calls in `cpu.py` by referencing the cached `fetch_raw_cpu_info()` directly.

---

## Upgrade Notes

No breaking changes. Standard installation and execution continues working as expected.
