# Architecture & Methodology

## Why EcoTrace?

Modern software teams face increasing pressure to quantify their carbon footprint — from **EU CSRD mandates** to internal ESG commitments. Most carbon tools rely on system-wide sensors that capture background OS noise, and measure at coarse intervals that miss bursty or async workloads.

**EcoTrace addresses this with process-scoped isolation and continuous 50ms sampling**, providing measurements that trace back to verified hardware specifications rather than broad category-level estimates.

| Strategy | Technical Implementation |
|---|---|
| **Scientific Foundation** | TDP-based energy estimation powered by the Boavizta database of 1,800+ CPU models. All measurements are derived from verified manufacturer specifications. |
| **Operational Performance** | 50ms daemon-thread sampling with process-scoped isolation. Negligible overhead for production environments. |
| **Regulatory Alignment** | Per-function gCO₂ audit trails with timestamped logs and PDF reports. Compatible with ESG, GHG Protocol, and EU CSRD reporting standards. |

---

## Comparison: EcoTrace vs Others

| **Feature** | **EcoTrace v0.8.0** | CodeCarbon | CarbonTracker |
|---|:---:|:---:|:---:|
| **API Style** | ✅ One-line `@track` | ✅ Decorator + Context | ❌ Manual |
| **Granularity** | ✅ Per-function | ⚠️ Session-level | ⚠️ Epoch-level |
| **Process Isolation** | ✅ Isolated | ❌ System-wide | ❌ System-wide |
| **Continuous Sampling** | ✅ **50ms** threads | ⚠️ 15s intervals | ❌ Point-in-time |
| **AI Insights** | ✅ Gemini-powered | ❌ | ❌ |
| **GPU Support** | ✅ Tri-Vendor | ⚠️ NVIDIA only | ⚠️ NVIDIA only |
| **Zero Config** | ✅ Full auto-detect | ⚠️ Config required | ⚠️ Config required |

### Key Differentiators

*   **System Noise Filtration:** EcoTrace isolates to the exact `psutil.Process()` and its children, reporting only your code's incremental carbon footprint.
*   **Continuous 50ms Micro-sampling:** Accurately captures bursty web server requests and async I/O waits.
*   **Fail-Safe Architecture:** When permissions are missing or environment is virtualized, EcoTrace gracefully falls back to static estimations.

---

## The Science

EcoTrace implements a **TDP-based energy estimation model**:

```
Energy (Wh) = TDP (W) × CPU Utilization (%) × Duration (s) / 3600
Carbon (gCO₂) = Energy (kWh) × Carbon Intensity (gCO₂/kWh)
```

### Formulas
$$E_{total} = E_{cpu} + E_{ram}$$
*   **CPU Energy ($E_{cpu}$):** `TDP (W) * (Utilization% / 100) * Duration (s) / 3600`
*   **RAM Energy ($E_{ram}$):** `RAM_Factor (W/GB) * Memory_Usage (GB) * Duration (s) / 3600`
*   **Carbon ($gCO_2$):** `(E_{total} / 1000) * Carbon_Intensity (gCO_2/kWh)`
