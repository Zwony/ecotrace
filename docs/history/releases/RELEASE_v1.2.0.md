# Release Notes — v1.2.0

**Released:** 2026-05-31
**Type:** Feature Release — ML/AI Tracking, Windows NVML Compatibility & Stability Fixes

---

## Summary

v1.2.0 introduces the brand-new **`EcoTraceML`** tracking engine specifically designed for measuring the energy consumption and carbon footprint of machine learning and AI model training sessions. It also delivers critical compatibility fixes for NVIDIA NVML on Windows, lazy-loads optional AI dependencies, and fixes Pylance type warnings.

---

## Key Features

### 1. Dedicated Machine Learning Tracker (`EcoTraceML`)
Introducing `EcoTraceML` (available as a context manager and the `@ecotrace_ml` decorator) to measure CPU, GPU, and RAM energy consumption during ML training runs with millisecond precision:
- **Asynchronous Sampling:** A background thread polls hardware utilization and power usage continuously.
- **Automatic Summary Reports:** Generates standard Markdown summaries and detailed PDF/CSV reports.
- **Parameters Supported:** Configurable metrics such as epoch size, batch size, and dataset size.

```python
from ecotrace import EcoTraceML

with EcoTraceML(project_name="ImageClassifier") as tracker:
    # Your model training loop here
    pass
```

### 2. Enhanced NVIDIA NVML Windows Compatibility
- **DLL Path Injection:** The GPU utility now dynamically searches for `nvml.dll` within `Program Files\NVIDIA Corporation\NVSMI` and `System32` and appends it to the PATH, resolving import issues on Windows.
- **Driver Decode Fix:** Safe fallback UTF-8 decoding for newer NVIDIA driver queries returning binary GPU names.

### 3. FPDF & Pylance Type Safety
- Modified PDF reporting methods to use positional arguments for cell text instead of the `txt` keyword argument, preventing runtime type warnings and strict Pylance checking errors.

### 4. Lazy-loading AI Extensions
- Lazy-loaded `google-generativeai` inside its specific invocation scope. This prevents `ModuleNotFoundError` when importing `ecotrace` on environments where the `[ai]` optional dependency extra is not installed.

### 5. Verified & Tested
- Added `example_ml.py` for illustrating the new ML training telemetry.
- Added comprehensive unit tests under `tests/test_ml.py`.

---

## Installation

```bash
pip install ecotrace==1.2.0
```

---

I would like to thank @batuhanyilmaz1 for his interest, help, and for leading the release of this version
