# Release Notes — v0.5.0

**Release Date:** 2026-03-28 **Type:** Minor Release

---

## Overview

v0.5.0 delivers high-precision hardware analysis with core-aware CPU normalization, deep RAM generation tracking, optional Gemini AI insights, and full Apple Silicon support.

---

## Added

**Smart Core Normalization**

A core-aware utilization tracking system properly scales across multi-core processors (1 to 128+ logical cores). This eliminates the utilization inflation effect in multi-threaded Python applications and ensures scientific accuracy for real-world production workloads.

**RAM Generation Tracking**

EcoTrace now detects RAM type (DDR4, DDR5, LPDDR) and clock speed to apply type-specific watt-factors using RSS-based recursive process tracking. Energy estimation for data-heavy tasks is significantly more accurate as a result.

**Gemini AI Insights (Beta)**

Optional integration with Google Gemini AI. When enabled, PDF reports include:

- Hardware-aware optimization recommendations tailored to the specific CPU and GPU model.
- Pythonic refactoring suggestions (async, vectorization, library-level swaps) to reduce carbon spikes.
- Actionable sustainability advice embedded directly in the audit report.

Requires `pip install ecotrace[ai]` .

**Apple Silicon Support**

Full native support for M1, M2, and M3 series architectures with specific power profile mappings.

---

## Architectural Improvements

- Engine refactored into distinct `cpu` , `gpu` , and `ram` intelligence modules.
- Monitoring daemon hardened to ensure minimal impact on production performance.
- Strict input validation for `gpu_index` and `region_code` parameters.

---

## How to Upgrade

```
pip install --upgrade ecotrace
```
