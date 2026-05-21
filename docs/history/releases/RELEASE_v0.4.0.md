# Release Notes — v0.4.0

**Release Date:** 2026-03-20 **Type:** Minor Release — Enterprise Hardening

---

## Overview

v0.4.0 is a comprehensive hardening release. Every layer of the library has been reinforced for thread safety, crash resilience, documentation coverage, and packaging correctness.

---

## Added

**Thread-Safe Carbon Accumulation**

`self.total_carbon` is now protected by `threading.Lock()` via the new `_accumulate_carbon()` method. This resolves a read-modify-write race condition that existed across three call sites when `@track` or `@track_gpu` decorators were used from concurrent threads. CSV audit logging is also serialized under the same lock to prevent interleaved rows.

**Crash-Proof Decorators and Input Validation**

- `measure()` , `measure_async()` , and `track_gpu()` — all post-execution carbon calculations are now wrapped in `try/except` . If sampling or computation fails mid-execution (for example, a GPU driver unloading), the function's return value is always preserved and a warning is logged.
- Invalid `region_code` values fall back to `"TR"` with a warning. Negative `gpu_index` values default to `0` . Invalid `carbon_limit` values are disarmed gracefully.
- `_gpu_monitor_worker()` now checks for `None` handles before entering the NVML sampling loop, protecting against cases where the GPU was detected at init but became unavailable.

**Google-Style Docstrings**

All 25 public methods now have complete Google-style docstrings with `Args` , `Returns` , and `Raises` sections.

---

## Updated

**Internal Refactoring**

- 12 magic numbers extracted into named class constants: `DEFAULT_CPU_TDP_W` , `MONITOR_INTERVAL_S` , `SAMPLE_BUFFER_SIZE` , `SECONDS_PER_HOUR` , `WATTS_PER_KILOWATT` , `FULL_UTILIZATION_PERCENT` , and others.
- The `TDP x utilization x duration / 3600` energy formula, previously duplicated in 3 locations, is now centralized in `_compute_carbon()` .
- New helper methods: `_sanitize_for_pdf()` , `_accumulate_carbon()` , `_validate_region_code()` , `_resolve_carbon_intensity()` , `_load_gpu_tdp_defaults()` .
- GPU TDP defaults moved to `constants.json` under `GPU_TDP_DEFAULTS` for external configurability.

**Packaging**

- `MANIFEST.in` updated to include `*.csv` data files alongside `*.json` .
- `pyproject.toml` package-data updated to ship the Boavizta CPU specification database in wheels.

---

## Test Results

```
29 passed, 1 skipped (pre-existing lru_cache/mock conflict)
```

---

## Migration from v0.3.x

This is a fully backward-compatible upgrade. No API changes were introduced.

```
pip install --upgrade ecotrace
```

The only behavioral change: invalid `region_code` and `gpu_index` values now produce warnings and fall back to safe defaults instead of silently proceeding.

---

**Full Changelog:** https://github.com/Zwony/ecotrace/compare/v0.3.5...v0.4.0
