# Release Notes — v1.1.2

**Released:** 2026-05-21
**Type:** Patch — Stability & Integration Fixes

---

## Summary

v1.1.2 is a quality-of-life and stability patch releasing critical fixes for exceptions handling, reporting tools, and RAM/CPU auto-detection routines. It also introduces one breaking change renaming the Django middleware for naming consistency.

---

## Breaking Changes

### Django Middleware Renaming
For naming consistency across integrations, the Django middleware class has been renamed to **`EcoTraceDjangoMiddleware`** and its module location updated to `ecotrace.middleware.django`. The FastAPI `EcoTraceMiddleware` remains unchanged.

```python
# Old (v1.1.0)
MIDDLEWARE = [
    "ecotrace.middleware.django.EcoTraceMiddleware",
    ...
]

# New (v1.1.2)
MIDDLEWARE = [
    "ecotrace.middleware.django.EcoTraceDjangoMiddleware",
    ...
]
```

---

## Bug Fixes & Engine Improvements

### 1. Robust Exception Propagation
In `measure` and `measure_async` decorators/managers, user exceptions are now guaranteed to propagate after measurement teardown. Any internal EcoTrace telemetry errors during teardown are caught and handled, preventing them from masking original application failures.

### 2. Session atexit Optimization
Replaced per-instance registration of `atexit` handlers with a class-level handler tracking active `WeakSet` instances, reducing clean-up overhead and preventing memory retention issues during runtime restarts.

### 3. RAM & CPU Hardware Detection
- **Windows:** Upgraded to use PowerShell `Get-CimInstance` to retrieve RAM info, deprecating `wmic` usage which could trigger security or deprecation warnings on newer Windows editions.
- **Linux:** `dmidecode` is run without `sudo` first. If output is empty, it attempts `sudo -n` for passwordless execution.
- **CPU Info Caching:** The caching logic was improved to reuse `fetch_raw_cpu_info()` results instead of performing redundant `cpuinfo` calls.

### 4. PDF & CSV Reporting
- `generate_pdf_report` now accepts custom `log_path`.
- CSV report parser now correctly resolves columns via `DictReader` column names instead of hardcoded indexes, improving durability against log schema modifications.

### 5. Dependency & Versioning Tweaks
- **Gemini AI:** `google.generativeai` package is now lazy-loaded inside `get_gemini_insights()`, avoiding unnecessary startup delays when AI features are not used.
- **User Agent:** Resolved from installed package version with appropriate fallback values.
- **Update Checker:** Added safety check to return `False` if parsing version strings fails.
- Restored the default log level to `WARNING` to reduce terminal noise.

---

## Installation

```bash
pip install ecotrace==1.1.2
```
