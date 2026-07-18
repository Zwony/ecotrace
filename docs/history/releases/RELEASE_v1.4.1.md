# Release Notes — v1.4.1

**Released:** 2026-07-18  
**Type:** Patch Release — 7 bug fixes, zero breaking changes  

---

## Summary

v1.4.1 is a patch release addressing multiple edge-case bugs, linter/static analysis warnings, and dynamic versioning issues identified in v1.4.0. It improves exception safety in code blocks, normalizes GPU reports, and resolves unresolved import warnings in environments without optional web dependencies installed.

---

## Resolved Issues & Bug Fixes

### 1. Exception Safety in `track_block()`
Restructured the `track_block()` context manager using a `try/finally` block. This ensures that session duration and carbon metrics are cleanly calculated and logged even if the wrapped code blocks raise user exceptions, aligning it with the robust exception-handling design of `measure()`.

### 2. GPU Chart Data Normalization
Normalized the `_gpu_samples` structure inside the core engine's PDF generator (`generate_pdf_report`). The core continuous hardware monitor tracks metrics using 3-tuples `(timestamp, utilization, power)`. The PDF reporting module now filters and maps these to 2-tuples `(timestamp, utilization)` before rendering to prevent visual plotting and parsing errors.

### 3. Django Middleware Renaming
Renamed the middleware class defined in `middleware/django.py` from `EcoTraceMiddleware` to `EcoTraceDjangoMiddleware` to perfectly reflect the migration guidelines documented in v1.1.2. A backward-compatible alias `EcoTraceMiddleware` is preserved at module scope to prevent integration breakage.

### 4. Dynamic Dashboard Versioning
Replaced the hardcoded version in the live dashboard HTML footer. It now dynamically injects the package's current version (e.g. `v1.4.1`) retrieved directly from metadata at request resolution.

### 5. Format-Aware Export Filenames
The CLI `ecotrace export` command now determines the default output filename according to the selected format. Specifying `--csv` automatically defaults to `ecotrace_export.csv` rather than confusingly writing CSV data to `ecotrace_report.json`.

### 6. Dynamic Web Imports (No Static Warnings)
Refactored `middleware/django.py` to lazily and dynamically load optional dependencies (`django` and `asgiref`) using `importlib`. This removes critical 'Unresolved Import' red alerts inside IDEs and static analyzers for developers using EcoTrace without standard web framework libraries in their environment.

### 7. Corrected GPU Energy Accumulation
Initialized the `total_energy_kwh` property inside the main engine constructor. This permits cumulative GPU/ML tracking contexts to correctly increment the total session energy metrics across consecutive training run boundaries.

---

## Upgrade Instructions

This is a non-breaking patch release. Upgrade via pip:

```bash
pip install --upgrade ecotrace
```
