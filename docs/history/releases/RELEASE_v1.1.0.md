# Release Notes — v1.1.0

**Released:** 2026-05-19
**Type:** Minor — Backwards-Compatible Feature Release

---

## Summary

v1.1.0 brings EcoTrace into the enterprise observability ecosystem. This release focuses on two production-grade integrations that allow organizations to route carbon metrics directly into their existing monitoring infrastructure and track emissions from their full Django and Celery application stack.

---

## New Features

### 1. OpenTelemetry (OTel) Exporter

EcoTrace can now push carbon metrics directly into any OpenTelemetry-compatible observability platform — **Grafana, Datadog, New Relic, Prometheus**.

```python
from ecotrace import EcoTrace
from ecotrace.exporters import OTelExporter

eco = EcoTrace(region_code="DE")
OTelExporter(ecotrace_instance=eco)  # auto-registers
```

A counter metric named `ecotrace.carbon.emitted` (unit: `g`) is created with two attributes per measurement:

- `ecotrace.function` — the name of the tracked function or block
- `ecotrace.region` — the grid intensity region code

Exporter dispatch is fully **non-blocking**: measurements are submitted to a 2-worker `ThreadPoolExecutor` so no slow telemetry backend can delay user code.

**Install:** `pip install ecotrace[otel]`

---

### 2. Django Middleware

Full WSGI and ASGI support for tracking carbon per HTTP request in Django applications.

```python
# settings.py
MIDDLEWARE = [
    "ecotrace.middleware.django.EcoTraceMiddleware",
    ...
]

# Optional settings
ECOTRACE_LOG_CSV = True   # log each request to ecotrace_log.csv
```

Every response receives two injected headers:
- `X-Eco-Carbon-Emitted` — carbon footprint in gCO2
- `X-Eco-Duration` — request duration in seconds

The middleware never interferes with 4xx/5xx responses — exceptions propagate naturally.

**Install:** `pip install ecotrace[web]`

---

### 3. Celery Plugin

Track carbon emissions per background task with automatic signal integration.

```python
from ecotrace import EcoTrace
from ecotrace.plugins.celery import EcoTraceCelery

eco = EcoTrace(region_code="US")
EcoTraceCelery(ecotrace_instance=eco, log_to_csv=True)
```

Connects to four Celery worker signals:

| Signal | Purpose |
|--------|---------|
| `task_prerun` | Start CPU monitor, stamp start time |
| `task_postrun` | Finalize measurement, log emissions |
| `task_retry` | Finalize current attempt independently (**prevents double-counting**) |
| `task_revoked` | Clean up state on kill/revoke (**prevents memory leak**) |

**Install:** `pip install ecotrace[celery]`

---

## Core Engine Changes

- **`EcoTrace.add_exporter(exporter)`** — New public API to register any object implementing `.export(carbon_emitted, func_name, duration, region)`.
- **Thread-safe exporter dispatch** — Exporters run on a dedicated 2-worker `ThreadPoolExecutor` to prevent blocking.
- **Graceful shutdown** — `_exporter_pool.shutdown(wait=True)` is called on process exit to flush all in-flight export tasks before the process terminates.

---

## Installation

```bash
# Core only
pip install ecotrace==1.1.0

# With OTel support
pip install "ecotrace[otel]==1.1.0"

# With Django + Celery
pip install "ecotrace[web,celery]==1.1.0"

# Everything
pip install "ecotrace[all]==1.1.0"
```

---

## Bug Fixes

- Fixed GPU TDP resolution to use `nvmlDeviceGetPowerManagementLimit` (runtime limit) instead of `nvmlDeviceGetPowerManagementDefaultLimit` (factory cap), which caused over-estimation on power-capped GPUs (e.g. throttled data centre A100s).

---

## What's Next — v1.2.0

- **Sampling Mode** — `@eco.track(sample_rate=0.1)` for statistical measurement at high call frequencies, removing the overhead barrier for adoption in high-throughput production services.
