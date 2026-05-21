# Release Notes — v1.1.2

**Release Date:** 2026-05-21 **Type:** Patch Release

---

## Overview

v1.1.2 is a reliability and compatibility patch. It fixes session-summary registration, measurement exception handling, hardware detection on Windows and Linux, version metadata, and Django middleware naming without changing FastAPI middleware APIs.

---

## Fixed

- **Class-level atexit:** Session summaries use a single `atexit` handler and a `WeakSet` of instances instead of per-instance registration.
- **measure / measure_async:** User exceptions propagate after teardown; measurement failures no longer mask or replace raised errors.
- **PDF reports:** `generate_pdf_report` accepts `log_path` and reads CSV rows by column name via `DictReader`.
- **Lazy Gemini import:** `google.generativeai` loads only inside `get_gemini_insights`, reducing import cost when AI is unused.
- **Windows RAM:** Replaced deprecated `wmic` with PowerShell `Get-CimInstance Win32_PhysicalMemory`.
- **Linux RAM:** Runs `dmidecode -t memory` without sudo first; retries with `sudo -n` only when output is empty (non-interactive sudo may still fail).
- **CPU detection:** `get_cpu_info` reuses cached `fetch_raw_cpu_info()` instead of a second `cpuinfo` call.
- **USER_AGENT:** Built dynamically from installed package version (`importlib.metadata`), with fallbacks.
- **Logger default:** Restored production-safe `WARNING` level.
- **Update checker:** `_is_newer_version` returns `False` on parse failure instead of treating unequal strings as upgrades.

---

## Changed (Breaking)

- **Django middleware rename:** `EcoTraceMiddleware` in `ecotrace.middleware.django` is now `EcoTraceDjangoMiddleware` to avoid clashing with FastAPI's `EcoTraceMiddleware`.

Update Django `MIDDLEWARE` settings:

```python
MIDDLEWARE = [
    # ...
    "ecotrace.middleware.django.EcoTraceDjangoMiddleware",
]
```

FastAPI examples remain `ecotrace.middleware.fastapi.EcoTraceMiddleware`.

---

## Updated

- Version bumped to `1.1.2` in `pyproject.toml` and `ecotrace.__init__`.
