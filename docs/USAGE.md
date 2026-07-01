# Advanced Usage Guide

---

## Pausable Tracking (`pause()` / `resume()`)

Temporarily disable carbon tracking to exclude setup, teardown, or data loading from your measurements.

```python
from ecotrace import EcoTrace

eco = EcoTrace(region_code="TR")

eco.pause()
load_dataset()       # not measured
eco.resume()

@eco.track
def run_model():
    ...              # measured

run_model()
```

The paused duration is automatically excluded from `get_summary()` totals.

---

## Run Comparison (`ecotrace diff`)

Compare any two runs side-by-side to verify whether a code change reduced emissions.

```bash
# Compare two specific run IDs
ecotrace diff abc123def456 789012abc345

# Compare the two most recent runs (CI/CD shortcut)
ecotrace diff --latest
```

Output shows per-function call counts, duration delta, and gCO2 delta (absolute + percentage).

---

## Webhook Exporter

Stream carbon metrics to any webhook in real-time — Slack, MS Teams, Discord, or a custom backend.

```python
from ecotrace import EcoTrace
from ecotrace.exporters.webhook import WebhookExporter

eco = EcoTrace(region_code="TR")
WebhookExporter(
    eco,
    url="https://hooks.slack.com/services/...",
    headers={"Authorization": "Bearer token"}
)
```

Each emission event sends a JSON payload with `function`, `carbon_gco2`, `duration_s`, `region`, `run_id`, and `run_label`.

---

## Log Maintenance (`ecotrace clean` & `ecotrace reset`)

Keep your audit CSV lean with built-in log rotation commands.

```bash
# Keep only the last 10 runs (creates .bak backup automatically)
ecotrace clean --keep-runs 10

# Delete all entries before a specific date
ecotrace clean --before 2026-06-01

# Delete the log file entirely (non-interactive)
ecotrace reset --yes
```

---

## Filtered CSV Export

Export a filtered subset of your audit log as CSV.

```bash
# Export a single run
ecotrace export --csv -o run_report.csv --run abc123def456

# Export a specific function across all runs
ecotrace export --csv -o func_report.csv --func "run_model"
```

---

## Decorator Tracking

### `@eco.track` — Function-Level Monitoring

The primary instrumentation method. Wraps synchronous functions to measure CPU, RAM, and GPU energy per call.

```python
from ecotrace import EcoTrace

eco = EcoTrace(region_code="DE")

@eco.track
def run_model():
    ...

run_model()
print(f"Total carbon: {eco.total_carbon:.6f} gCO2")
```

### `@eco.track_gpu` — GPU Monitoring

Supports NVIDIA, AMD, and Intel GPUs with real-time utilization sampling.

```python
eco = EcoTrace(gpu_index=0)

@eco.track_gpu
def gpu_inference():
    ...
```

### `eco.track_block()` — Context Manager

Instruments an arbitrary block of code without decorating a function.

```python
with eco.track_block("data_pipeline"):
    process_data()
```

### Async Support

EcoTrace natively supports `async` functions via `track_async`:

```python
import asyncio

eco = EcoTrace(region_code="SE")

@eco.track_async
async def fetch_data():
    await asyncio.sleep(1)

asyncio.run(fetch_data())
```

### `eco.compare()` — Side-by-Side Analysis

Runs two functions under identical conditions and returns a comparative carbon report.

```python
result = eco.compare(bubble_sort, quick_sort)
# result contains per-function carbon, duration, and CPU utilization
```

---

## Carbon Budget Mode

Set a hard limit and receive alerts when thresholds are approached or exceeded.

```python
eco = EcoTrace(
    region_code="TR",
    carbon_limit=5.0,
    on_budget_exceeded=lambda total, limit: print(f"Exceeded: {total:.4f}/{limit:.4f} gCO2")
)

@eco.track
def training_pipeline():
    ...

training_pipeline()
print(f"Remaining budget: {eco.remaining_budget:.4f} gCO2")
```

Alerts fire at **80%** (warning) and **100%** (exceeded) of the configured limit.

---

## Web Framework Integrations

### Flask

`EcoTraceFlask` injects `X-Eco-Carbon-Emitted` and `X-Eco-Duration` response headers on every request.

```python
from flask import Flask
from ecotrace.middleware.flask import EcoTraceFlask

app = Flask(__name__)
EcoTraceFlask(app)  # attaches before_request / after_request hooks

@app.route("/predict")
def predict():
    return "ok"
```

To log each request to the audit CSV:

```python
EcoTraceFlask(app, log_to_csv=True)
```

You can also pass an existing `EcoTrace` instance to share state:

```python
from ecotrace import EcoTrace
eco = EcoTrace(region_code="DE", carbon_limit=100.0)
EcoTraceFlask(app, ecotrace_instance=eco)
```

### FastAPI / Starlette

`EcoTraceMiddleware` is an ASGI-compatible middleware that measures carbon per request.

```python
from fastapi import FastAPI
from ecotrace.middleware.fastapi import EcoTraceMiddleware

app = FastAPI()
app.add_middleware(EcoTraceMiddleware)

@app.get("/predict")
async def predict():
    return {"status": "ok"}
```

With CSV logging and a shared instance:

```python
from ecotrace import EcoTrace
eco = EcoTrace(region_code="US", carbon_limit=50.0)
app.add_middleware(EcoTraceMiddleware, ecotrace_instance=eco, log_to_csv=True)
```

Both middlewares require the `[web]` extra:

```bash
pip install ecotrace[web]
```

---

## pytest Integration

The EcoTrace pytest plugin measures carbon emissions per test and prints a summary at the end of the session.

**Enable with the `--ecotrace` flag:**

```bash
pytest --ecotrace
```

**Example terminal output:**

```
========================= EcoTrace: Carbon Infrastructure Audit =========================
Total Test Suite Duration : 4.21 s
Total Carbon Emissions    : 0.00018340 gCO2

Top 3 Most Carbon-Heavy Tests:
------------------------------------------------------------
1. tests/test_core.py::test_heavy_workload
   [CO2: 0.00012110 gCO2 | Duration: 2.81s | CPU: 74.3%]
2. tests/test_report.py::test_pdf_generation
   [CO2: 0.00004200 gCO2 | Duration: 1.02s | CPU: 31.1%]
3. tests/test_cli.py::test_gate_exit_code
   [CO2: 0.00002030 gCO2 | Duration: 0.38s | CPU: 18.7%]
------------------------------------------------------------
```

> **Note:** Parallel test execution via `pytest-xdist` will aggregate emissions across workers sharing the same process. Sequential execution is recommended for accurate per-test measurements.

---

## Live Grid API

Fetch real-time carbon intensity from [Electricity Maps](https://www.electricitymaps.com/):

```python
eco = EcoTrace(region_code="DE", grid_api_key="YOUR_KEY")
```

When a valid API key is provided, EcoTrace queries live grid data and falls back to static IEA 2024 averages on any network or authentication failure.

---

## AI-Powered Insights

Generate actionable optimization advice via Google Gemini:

```python
eco = EcoTrace(api_key="YOUR_GEMINI_API_KEY")
eco.generate_pdf_report("smart_audit.pdf")
```

The report includes:

- **Vectorization advice** — detects loops that could be replaced with NumPy operations.
- **Architecture tuning** — suggests `asyncio` for I/O-bound tasks.
- **Carbon equivalences** — converts gCO2 values to Google searches, LED bulb minutes, or car kilometres.

Requires the `[ai]` extra:

```bash
pip install ecotrace[ai]
```

---

## Benchmarks

The following figures were recorded on a 13th Gen Intel Core i7-13700H (20 cores, 45W TDP) in the TR region (475 gCO2/kWh).

### Lightweight Workload

- CPU Utilization: `4.8%`
- Carbon Footprint: `0.000574 gCO2`

### Heavyweight Workload (20-Core Stress)

- CPU Utilization: `77.0%`
- Carbon Footprint: `0.414649 gCO2`
