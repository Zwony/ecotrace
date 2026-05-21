# Release Notes — v0.9.0

**Release Date:** 2026-04-30 **Type:** Minor Release

---

## Overview

v0.9.0 delivers a significant accuracy upgrade through direct hardware energy counter monitoring on Linux (RAPL) and a non-linear Boavizta load curve model for Windows and macOS. A new hybrid engine automatically selects the most precise measurement method available on the current system.

---

## Added

**Exact Mode — RAPL (Linux)** On Linux kernels with `intel_rapl` or `intel_rapl_msr` modules loaded, EcoTrace reads energy counters directly from `/sys/class/powercap/` . This method has 0% deviation from physical power consumption.

```
[EcoTrace] INFO: Energy Sensor : RAPL Direct (Exact Mode)
```

**Advanced Power Modeling — Boavizta Load Curves (Windows / macOS)** Replaces the previous linear TDP estimation with non-linear load curves derived from the Boavizta database. Power draw is now calculated across idle, average, and peak load segments, providing significantly more accurate results for workloads that are not CPU-bound for the full measurement window.

**Hybrid Energy Engine** Automatic hardware detection now selects the measurement method in the following priority order:

1. RAPL (Linux, direct hardware counter)
2. Boavizta advanced estimation (Windows / macOS)
3. Linear TDP fallback (any platform, when Boavizta lookup fails)

The selected engine is reported in the initialization banner:

```
[EcoTrace] INFO: Energy Sensor : Boavizta Advanced Estimation
```

---

## Updated

- Version bumped to `0.9.0` across `pyproject.toml` , `__init__.py` , and `config.py` .
