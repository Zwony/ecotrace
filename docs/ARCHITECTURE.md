# Architecture and Methodology

## Overview

Modern software teams face increasing pressure to quantify their carbon footprint — from EU CSRD mandates to internal ESG commitments. Most carbon tools rely on system-wide sensors that capture background OS noise and measure at coarse intervals that miss bursty or async workloads.

EcoTrace addresses this with process-scoped isolation and continuous 50ms sampling, providing measurements that trace back to verified hardware specifications rather than broad category-level estimates.

| Strategy | Technical Implementation |
|---|---|
| **Scientific Foundation** | TDP-based energy estimation powered by an expanded database of 6,980+ unique CPU models (100% verified TDP coverage). All measurements are derived from verified manufacturer specifications. |
| **Operational Performance** | 50ms daemon-thread sampling with process-scoped isolation. Negligible overhead for production environments. |
| **Regulatory Alignment** | Per-function gCO2 audit trails with timestamped logs and PDF reports. Compatible with ESG, GHG Protocol, and EU CSRD reporting standards. |

---

## Comparison: EcoTrace  vs Alternatives

| **Feature** | **EcoTrace v1.5.1** | CodeCarbon | CarbonTracker |
|---|:---:|:---:|:---:|
| **API Style** | One-line `@track` | Decorator + Context | Manual |
| **Granularity** | Per-function | Session-level | Epoch-level |
| **Process Isolation** | Isolated | System-wide | System-wide |
| **Continuous Sampling** | **50ms** threads | 15s intervals | Point-in-time |
| **Budget Enforcement** | Built-in | No | No |
| **CI/CD Gate** | Built-in | No | No |
| **AI Insights** | Gemini-powered | No | No |
| **GPU Support** | Tri-Vendor | NVIDIA only | NVIDIA only |
| **Zero Config** | Full auto-detect | Config required | Config required |

### Key Differentiators

- **System Noise Filtration:** EcoTrace isolates to the exact `psutil.Process()` and its children, reporting only the incremental carbon cost of your code — not OS background noise.
- **Continuous 50ms Micro-sampling:** Accurately captures bursty web server requests and async I/O workloads.
- **Fail-Safe Architecture:** When permissions are missing or the environment is virtualized, EcoTrace gracefully falls back to static estimations without interrupting the application.
- **Carbon Budget Enforcement:** Configurable `carbon_limit` with two-tier alerts (80% warning, 100% exceeded) and optional callback hooks.

---

## Energy Model

EcoTrace implements a TDP-based energy estimation model:

```
Energy (Wh) = TDP (W) x CPU Utilization (%) x Duration (s) / 3600
Carbon (gCO2) = Energy (kWh) x Carbon Intensity (gCO2/kWh)
```

### Formulas

$$E_{total} = E_{cpu} + E_{ram}$$

- **CPU Energy ($E_{cpu}$):** `TDP (W) * (Utilization% / 100) * Duration (s) / 3600`
- **RAM Energy ($E_{ram}$):** `RAM_Factor (W/GB) * Memory_Usage (GB) * Duration (s) / 3600`
- **Carbon ($gCO_2$):** `(E_{total} / 1000) * Carbon_Intensity (gCO_2/kWh)`

### Differential Tracking

Starting from v1.0.1, EcoTrace subtracts a measured idle CPU baseline from all readings. This ensures that only the energy attributable to user code is reported, eliminating OS scheduler noise and background service overhead.

---

## Measurement Accuracy & Empirical Validation

EcoTrace combines hardware-level register interfaces with a calibrated non-linear piecewise estimation model derived from empirical research (Boavizta load curve):

1. **Hardware Mode (Linux RAPL / Apple Silicon `powermetrics`):** Direct hardware measurement via Intel/AMD RAPL energy registers (`/sys/class/powercap/intel-rapl`) and macOS `powermetrics`.
2. **Calibrated Estimation Mode (Cross-Platform Fallback):** When low-level kernel counters are restricted, EcoTrace applies a piecewise non-linear model accounting for static leakage power (12% baseline) and non-linear dynamic scaling.

### Empirical Validation Metrics against Hardware Counters (RAPL)

| Metric | Expected Value (Linux + RAPL) | Standard Target |
| :--- | :--- | :--- |
| **Mean Absolute Percentage Error (MAPE)** | $\le 15.0\%$ | $< 15.0\%$ |
| **Coefficient of Determination ($R^2$)** | $\ge 0.90$ | $> 0.900$ |
| **Root Mean Squared Error (RMSE)** | $< 5.0\text{ Watts}$ | $< 5.0\text{ Watts}$ |

These are the typical accuracy bounds observed when EcoTrace's piecewise model is compared against direct Intel/AMD RAPL register readings on Linux. On Windows or other systems where RAPL is unavailable, the [validation harness](../benchmarks/articles/07_accuracy_validation.md) uses a synthetic non-linear reference curve, which produces a wider error distribution because it is a model-vs-model comparison rather than a model-vs-hardware comparison.

For full experimental setups, statistical methodology, and the synthetic-mode limitations, refer to the [Accuracy Validation Benchmark](../benchmarks/articles/07_accuracy_validation.md).
