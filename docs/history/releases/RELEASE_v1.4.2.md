# Release Notes — v1.4.2

**Released:** 2026-07-21  
**Type:** Patch & Quality Release — 10 Bug Fixes, Web Platform Integration, Zero Breaking Changes  

---

## Highlight: Stream Real-Time Carbon Metrics to EcoTrace Web Dashboard

With **v1.4.2**, connecting your Python services and ML models to the **EcoTrace Cloud & Live Web Dashboard** at [ecotracelibrary.com](https://ecotracelibrary.com) is seamless using `WebhookExporter`. 

Stream function-level carbon footprints, execution durations, and hardware power draw directly to your personalized live dashboard in real time with your account's API key:

```python
from ecotrace import EcoTrace
from ecotrace.exporters import WebhookExporter

# Initialize EcoTrace engine
eco = EcoTrace(region_code="TR", carbon_limit=5.0)

# Connect to the EcoTrace Web Dashboard with your personal Ingestion Key
WebhookExporter(
    eco,
    url="https://ecotracelibrary.com/api/metrics/ingest",
    headers={"X-EcoTrace-Key": "ect_your_personal_key"}
)

@eco.track
def train_model():
    # Your CPU/GPU computation here
    pass

train_model()
```

👉 **Create a free account and sign in at [ecotracelibrary.com](https://ecotracelibrary.com) to generate your personal Ingestion Key and start monitoring your production services live!**

---

##  Resolved Issues & Bug Fixes in v1.4.2

### 1. `ram_info` Null Safety Guard
Guarded `_compute_carbon()` and initialization logging against `NoneType` and missing dictionary keys in `ram_info` to prevent runtime crash loops on custom or virtualized server environments.

### 2. Global Scope NVML Teardown Isolation
Removed explicit `pynvml.nvmlShutdown()` calls from instance `__del__` destructors. Global NVML state is now preserved for concurrent `EcoTrace` instances and multi-GPU telemetry contexts.

### 3. Exception Propagation Teardown Safety
Refactored error handling in `measure()` and `measure_async()` decorators to guarantee that original user exceptions are never masked by internal teardown or metrics calculation errors.

### 4. Live Dashboard Stored XSS Protection
Sanitized user inputs and measurement function names prior to DOM rendering in the live web dashboard interface.

### 5. Live Dashboard CORS Origin Restriction
Restricted the live dashboard's `Access-Control-Allow-Origin` header from permissive wildcard `*` to strict `localhost` origin.

### 6. GitHub Action CLI `--region` Support
Added `--region` flag support to the `ecotrace gate` subcommand required by the official `action.yml` GitHub Action pipeline.

### 7. Fail-Safe Updater Version Comparison
Replaced string inequality with integer tuple parsing for version comparison in `updater.py` when optional `packaging` dependency is absent.

### 8. Middleware Lazy Module Loading
Implemented module `__getattr__` in `middleware/__init__.py` to prevent eager imports of optional web frameworks (`django`, `flask`, `starlette`) until explicitly requested.

### 9. Extended RAM Power Modeling
Added architectural watt factors for DDR3, LPDDR4, LPDDR5, and UNKNOWN memory generations to `RAM_WATT_FACTORS`.

### 10. Configurable PDF Log Path
Added a configurable `log_file` parameter to `generate_pdf_report()` allowing users to render audit reports from custom CSV log locations.

---

##  Upgrade Instructions

This is a non-breaking patch release. Upgrade via PyPI:

```bash
pip install --upgrade ecotrace
```
