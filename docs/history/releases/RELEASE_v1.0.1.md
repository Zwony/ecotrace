# Release Notes — v1.0.1

**Release Date:** 2026-05-05 **Type:** Production/Stable Release

---

## Overview

v1.0.1 is the first production-stable release of EcoTrace. It shifts the library from passive measurement to active environmental accountability with carbon budget enforcement, CI/CD gate integration, differential tracking, and session summaries. Several critical bugs affecting exception handling, GPU monitoring, and packaging are resolved.

---

## Added

**Carbon Budget Enforcement** The `carbon_limit` parameter now actively enforces a carbon budget with two-tier alerts:

- **80% threshold** — warning logged automatically
- **100% threshold** — `on_budget_exceeded` callback invoked

```
eco = EcoTrace(
    region_code="TR",
    carbon_limit=5.0,
    on_budget_exceeded=lambda total, limit: print(f"Exceeded: {total:.4f}/{limit:.4f} gCO2")
)
```

**Differential Tracking** An idle CPU baseline is measured at startup and subtracted from all subsequent readings. Only the energy directly attributable to user code is reported.

**Session Summary** An `atexit` hook prints a formatted summary when the process exits:

```
=======================================================
  EcoTrace — Session Summary
=======================================================
  Duration       : 12.34s
  Functions      : 5 tracked
  Total Carbon   : 0.00312000 gCO2
  Region         : TR (475 gCO2/kWh)
  Budget         : 0.003120 / 5.000000 gCO2 (0.1%) [OK]
  Equivalent     : 0.4 min of LED bulb (10W)
=======================================================
```

**Carbon Equivalences** The `equivalence(gco2)` method converts abstract gCO2 values into human-readable comparisons:

- Google searches
- LED bulb minutes
- Smartphone charges
- Netflix streaming minutes
- Car kilometres

**CI/CD Carbon Gate** `ecotrace gate --budget <gCO2>` returns exit code 1 if accumulated emissions exceed the budget. Designed for GitHub Actions and GitLab CI.

```
- name: EcoTrace Carbon Gate
  uses: Zwony/ecotrace@v1.0.1
  with:
    budget: '10.0'
    region: 'US'
```

**`remaining_budget` Property** Programmatic access to the remaining carbon budget for external consumers such as IDE extensions and dashboards.

---

## Fixed

- **Exception swallowing** — `measure()` and `measure_async()` now re-raise user exceptions instead of silently returning `None` .
- **GPU `track_block` crash** — Fixed tuple unpacking error when computing GPU carbon in `track_block()` .
- **GPU chart crash** — Fixed 3-tuple unpacking in `report.py` GPU chart generation.
- **Packaging** — Added `ecotrace.middleware` and `ecotrace.plugins` to distribution packages.
- **Optional dependencies** — Moved `nvidia-ml-py` , `google-generativeai` , and `wmi` to optional extras ( `pip install ecotrace[gpu]` , `[ai]` , `[all]` ).

---

## Updated

- Logger default level changed from `WARNING` to `INFO` so the initialization banner is visible by default.
- Version bumped to `1.0.1` across `pyproject.toml` , `__init__.py` , and `config.py` .
