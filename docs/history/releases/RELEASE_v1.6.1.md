# Release Notes — v1.6.1

**Release Date:** September 18, 2026  
**Tag:** `v1.6.1`  
**PyPI Package Version:** `1.6.1`  

---

## Overview

EcoTrace **v1.6.1** introduces native **HuggingFace Transformers Trainer integration**, drop-in **CodeCarbon API compatibility** (`EmissionsTracker`), and **Academic Benchmark Case 08 (The Observer Effect)** comparing continuous 50ms process-scoped monitoring against coarse 15s system-wide polling. This release also establishes **Zenodo DOI archival metadata** for scientific citations and resolves all static type diagnostics across the academic benchmark suite.

---

## Key Improvements in v1.6.1

### 1. HuggingFace Transformers Integration (`ecotrace.callbacks.huggingface`)
- **Native Callback Handler:** Added `EcoTraceHuggingFaceCallback` supporting HuggingFace `Trainer` out-of-the-box.
- **Per-Step Telemetry Injection:** Injects instantaneous carbon emissions, dynamic power draw (W), and energy consumption into `state.log_history` on step intervals (`on_step_end`).
- **Epoch & Run Aggregation:** Summarizes total emissions at each epoch boundary and logs consolidated carbon footprints upon training completion (`on_train_end`).

### 2. CodeCarbon Drop-in Compatibility Layer (`ecotrace.tracker`)
- **Frictionless Migration:** Existing CodeCarbon users can migrate without modifying application logic via `from ecotrace import EmissionsTracker, OfflineEmissionsTracker, track_emissions`.
- **Full API Parity:** Implements `.start()`, `.stop()`, and property bindings (`final_emissions_data`, `duration_seconds`) mapped transparently to EcoTrace's process-isolated measurement engine.

### 3. Case 08: The Observer Effect Benchmark (`benchmarks/08_ecotrace_vs_codecarbon.py`)
- **Instrumentation Overhead & Architectural Trade-offs:** Evaluates the differences between tracking architectures. Demonstrates EcoTrace's lightweight footprint (+53% overhead on micro-workloads) designed for rapid lifecycle execution alongside architectures tailored for long-running multi-hour training runs.
- **Sampling Resolution Analysis:** Explores signal capture across different sampling intervals (50ms continuous vs. 15s periodic polling) during short computational bursts.
- **Comparative Study:** Published a comprehensive benchmark report with hardware snapshots and mathematical analysis (`benchmarks/articles/08_ecotrace_vs_codecarbon.md`).

### 4. Zenodo DOI Archival Integration (`.zenodo.json` & `CITATION.cff`)
- **Automated DOI Minting:** Added standardized `.zenodo.json` metadata for automated citable DOI assignment via Zenodo GitHub release integration.
- **Citation Metadata:** Updated `CITATION.cff` to v1.6.1 for direct academic referencing.

### 5. Benchmark Suite Standardization & Type Safety
- **Harmonized Benchmark Indexing:** Renamed initial benchmark to `01_pandas_vs_polars.py` and updated suite registry across `benchmarks/README.md`.
- **Zero IDE Diagnostics:** Fixed all 21 Pyrefly / Pyright / Pylance diagnostics across benchmark scripts and report generation utilities (correcting FPDF integer font sizes, loop variable bounds, and type narrowing).
- **Clean Git Hygiene:** Added blanket `*.csv` ignore patterns in `.gitignore`.

---

## Verification & Test Suite

- **100% Test Pass Rate:** All 151 unit and integration tests passed cleanly (including new tests for `EcoTraceHuggingFaceCallback` and `EmissionsTracker`).
- **Full Python Compatibility:** Verified across Python 3.8 through Python 3.14+.
