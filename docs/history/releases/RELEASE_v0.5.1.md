# Release Notes — v0.5.1

**Release Date:** 2026-03-28
**Type:** Patch Release

---

## Overview

v0.5.1 restores PDF visual reporting that regressed in v0.5.0 and refines the performance insight engine.

---

## Fixed

**Automated PDF Visuals**

`generate_pdf_report()` now automatically captures the full session monitoring data for CPU and GPU utilization charts. This restores a regression introduced in v0.5.0 where charts were omitted unless passed manually.

**GPU Visualization**

Restored and improved the GPU utilization chart for NVIDIA, AMD, and Intel hardware.

---

## Updated

**Balanced Performance Insights**

The internal recommendation engine now accounts for Smart Core Normalization. Optimization advice scales based on the system's core count, eliminating false-positive "Try batching" warnings for single-threaded tasks on high-core processors (Apple M3, Intel i9, etc.). Advice terminology now distinguishes accurately between single-thread intensive tasks and true high-multicore system-wide stress.

**Hardware Robustness**

Improved GPU detection logic for Intel Iris Xe and AMD integrated graphics, ensuring monitoring threads initialize correctly across all vendor classes.

---

## Internal Improvements

- Snapshotting of internal deques for PDF generation is now protected by monitoring locks.
- Fixed historical log parsing in the PDF generator to match the v0.5.1 multi-column CSV format.
- Execution-time alerts are now prioritized over utilization flags for more actionable output.

---

## How to Upgrade

```bash
pip install --upgrade ecotrace
```
