# Advanced Usage Guide

## Decorator Tracking

### `@eco.track` — Function-Level Monitoring

The primary instrumentation method. Wraps synchronous functions to measure CPU, RAM, and GPU energy per call.

```
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

```
eco = EcoTrace(gpu_index=0)

@eco.track_gpu
def gpu_inference():
    ...
```

### `eco.track_block()` — Context Manager

Instruments an arbitrary block of code without decorating a function.

```
with eco.track_block("data_pipeline"):
    process_data()
```

### Async Support

EcoTrace natively supports `async` functions via `track_async` :

```
import asyncio

eco = EcoTrace(region_code="SE")

@eco.track_async
async def fetch_data():
    await asyncio.sleep(1)

asyncio.run(fetch_data())
```

### `eco.compare()` — Side-by-Side Analysis

Runs two functions under identical conditions and returns a comparative carbon report.

```
result = eco.compare(bubble_sort, quick_sort)
# result contains per-function carbon, duration, and CPU utilization
```

---

## Carbon Budget Mode

Set a hard limit and receive alerts when thresholds are approached or exceeded.

```
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

### Flask {: #flask }

`EcoTraceFlask` injects `X-Eco-Carbon-Emitted` and `X-Eco-Duration` response headers on every request.

```
from flask import Flask
from ecotrace.middleware.flask import EcoTraceFlask

app = Flask(__name__)
EcoTraceFlask(app)  # attaches before_request / after_request hooks

@app.route("/predict")
def predict():
    return "ok"
```

To log each request to the audit CSV:

```
EcoTraceFlask(app, log_to_csv=True)
```

You can also pass an existing `EcoTrace` instance to share state:

```
from ecotrace import EcoTrace
eco = EcoTrace(region_code="DE", carbon_limit=100.0)
EcoTraceFlask(app, ecotrace_instance=eco)
```

### FastAPI / Starlette {: #fastapi-starlette }

`EcoTraceMiddleware` is an ASGI-compatible middleware that measures carbon per request.

```
from fastapi import FastAPI
from ecotrace.middleware.fastapi import EcoTraceMiddleware

app = FastAPI()
app.add_middleware(EcoTraceMiddleware)

@app.get("/predict")
async def predict():
    return {"status": "ok"}
```

With CSV logging and a shared instance:

```
from ecotrace import EcoTrace
eco = EcoTrace(region_code="US", carbon_limit=50.0)
app.add_middleware(EcoTraceMiddleware, ecotrace_instance=eco, log_to_csv=True)
```

### Django {: #django }

`EcoTraceDjangoMiddleware` tracks carbon per HTTP request for Django (WSGI and ASGI). This name is distinct from FastAPI's `EcoTraceMiddleware` in `ecotrace.middleware.fastapi`.

Add to `MIDDLEWARE` in `settings.py`:

```
MIDDLEWARE = [
    # ...
    "ecotrace.middleware.django.EcoTraceDjangoMiddleware",
]
```

Optional settings in `settings.py`:

```
ECOTRACE_INSTANCE = EcoTrace(region_code="DE", quiet=True, check_updates=False)
ECOTRACE_LOG_CSV = True
```

Install the web extra (includes Django):

```
pip install ecotrace[web]
```

Both middlewares require the `[web]` extra:

```
pip install ecotrace[web]
```

---

## pytest Integration {: #pytest-integration }

The EcoTrace pytest plugin measures carbon emissions per test and prints a summary at the end of the session.

**Enable with the `--ecotrace` flag:**

```
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

Fetch real-time carbon intensity from [Electricity Maps](https://www.electricitymaps.com/) :

```
eco = EcoTrace(region_code="DE", grid_api_key="YOUR_KEY")
```

When a valid API key is provided, EcoTrace queries live grid data and falls back to static IEA 2024 averages on any network or authentication failure.

---

## AI-Powered Insights

Generate actionable optimization advice via Google Gemini:

```
eco = EcoTrace(api_key="YOUR_GEMINI_API_KEY")
eco.generate_pdf_report("smart_audit.pdf")
```

The report includes:

- **Vectorization advice** — detects loops that could be replaced with NumPy operations.
- **Architecture tuning** — suggests `asyncio` for I/O-bound tasks.
- **Carbon equivalences** — converts gCO2 values to Google searches, LED bulb minutes, or car kilometres.

Requires the `[ai]` extra:

```
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
