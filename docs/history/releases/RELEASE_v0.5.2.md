# Release Notes — v0.5.2

**Release Date:** 2026-03-28 **Type:** Patch Release

---

## Overview

v0.5.2 unifies CPU and GPU monitoring under the standard `@track` decorator and delivers fully automated PDF report generation.

---

## Added

**Unified Multi-Resource Monitoring**

The standard `@track` decorator and `measure()` API now automatically detect and monitor GPU alongside CPU when hardware is available. Carbon emissions from both sources are aggregated into a single total in all reports.

**Automated Visual Reporting**

`generate_pdf_report()` now operates without any additional parameters. All CPU and GPU samples collected during the session are automatically included as high-resolution utilization charts in the generated report.

**Core-Aware Performance Insights**

False "Low CPU" warnings on high-core-count processors (such as the Intel i7-13700H with 20 logical cores) have been resolved. The analysis engine now computes dynamic thresholds based on the detected core count, and advice terminology has been updated to distinguish between single-thread intensive and high-multicore workloads.

---

## Internal Improvements

- CPU and GPU monitors can now run concurrently without blocking each other.
- All tracking methods ( `track` , `track_block` , `measure` ) share a unified carbon accumulation path.
- Resolved trailing sample loss in async tracking sessions.

---

## How to Upgrade

```
pip install --upgrade ecotrace
```
