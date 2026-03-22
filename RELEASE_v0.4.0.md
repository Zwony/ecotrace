# 🚀 EcoTrace v0.4.0 — Enterprise Hardening Release

> **This is the biggest update since EcoTrace's inception.** Every layer of the library has been hardened, documented, and repositioned for production deployment.

---

## ⚡ What's New

### 🔒 Enterprise Hardening — Thread-Safe Carbon Accumulation

`self.total_carbon` is now protected by `threading.Lock()` via the new `_accumulate_carbon()` method. This eliminates a **read-modify-write race condition** that existed across three call sites when `@track` or `@track_gpu` decorators were used from multiple threads. CSV audit logging is also serialized under the same lock to prevent interleaved rows.

### 🛡️ Reliability — Crash-Proof Decorators & Input Validation

- **`measure()`, `measure_async()`, `track_gpu()`** — All post-execution carbon calculations are now wrapped in `try/except`. If sampling or computation fails mid-execution (e.g., GPU driver unloads), the **function's return value is always preserved** and a warning is logged.
- **Input validation on `__init__`** — Invalid `region_code` values are caught and fall back to `"TR"` with a warning. Negative `gpu_index` values default to `0`. Invalid `carbon_limit` values are disarmed gracefully.
- **GPU monitor guard** — `_gpu_monitor_worker()` now checks for `None` handles before entering the NVML sampling loop, protecting against edge cases where the GPU was detected at init but became unavailable.

### 📖 Documentation — Google-Style Docstrings & High-Authority README

- **All 25 methods** now have full Google-style docstrings with `Args`, `Returns`, and `Raises` sections.
- **Complete README rewrite** — Repositioned from "lightweight tool" to "High-Precision, Production-Ready Carbon Tracking Engine." New sections include:
  - Science Behind EcoTrace (methodology)
  - Robustness & Safety (defensive design table)
  - Competitive comparison vs. CodeCarbon & CarbonTracker
  - EcoTrace Pro roadmap (Cloud Dashboard, ESG Reports, CI/CD integration)

### 🧹 Internal Refactoring — Clean Code Overhaul

- **12 magic numbers extracted** into named class constants: `DEFAULT_CPU_TDP_W`, `MONITOR_INTERVAL_S`, `SAMPLE_BUFFER_SIZE`, `SECONDS_PER_HOUR`, `WATTS_PER_KILOWATT`, `FULL_UTILIZATION_PERCENT`, and more.
- **Formula centralization** — The `TDP × utilization × duration / 3600` energy formula was duplicated in 3 places. New `_compute_carbon()` method eliminates all copies.
- **New helper methods** — `_sanitize_for_pdf()`, `_accumulate_carbon()`, `_validate_region_code()`, `_resolve_carbon_intensity()`, `_load_gpu_tdp_defaults()`.
- **GPU TDP defaults** moved to `constants.json` under `GPU_TDP_DEFAULTS` for external configurability.

### 📦 Packaging Improvements

- `MANIFEST.in` now includes `*.csv` data files alongside `*.json`.
- `pyproject.toml` package-data updated to ship the Boavizta CPU spec database in wheels.

---

## 📊 Test Results

```
29 passed, 1 skipped (pre-existing lru_cache/mock conflict)
```

All new functionality is verified. No regressions introduced.

---

## 🔄 Migration from v0.3.x

**This is a fully backwards-compatible upgrade.** No API changes. Simply update:

```bash
pip install --upgrade ecotrace
```

The only behavioral change: invalid `region_code` and `gpu_index` values now produce warnings and fall back to safe defaults instead of silently proceeding.

---

## 💚 What's Next

- ☁️ Cloud Dashboard Integration
- 🔗 AWS / Azure / GCP Native Monitoring
- 📊 Automated ESG Report Generation
- 🏢 Team & Organization Carbon Budgets
- 🔌 CI/CD Pipeline Integration

**Full Changelog**: https://github.com/Zwony/ecotrace/compare/v0.3.5...v0.4.0
