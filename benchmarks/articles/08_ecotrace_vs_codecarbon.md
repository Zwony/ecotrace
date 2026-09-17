# Case 08: The Observer Effect — Empirical Overhead & Metrology: EcoTrace vs. CodeCarbon

*A Comparative Evaluation of Instrumentation Latency, Process-Scoped Granularity, and Under-Reporting in Green Software Metrology.*

---

## Abstract

Software energy and carbon tracking libraries are designed to quantify emissions; however, by virtue of executing alongside the target workload, their measurement instrumentation inevitably alters execution characteristics — a phenomenon in software metrology known as the **Observer Effect** (Heisenbug dynamics). 

This benchmark presents an empirical head-to-head evaluation of **EcoTrace** vs. **CodeCarbon (v3.3.1)** on an identical deterministic workload ($2.5 \times 10^6$ arithmetic operations). We evaluate:
1. **Instrumentation Overhead & Latency Inflation**: Execution slowdown relative to an unmonitored baseline.
2. **Temporal Sampling Granularity**: High-frequency continuous sampling (50 ms) vs. coarse-grained periodic polling (15,000 ms).
3. **Telemetry Scope & Under-Reporting Risk**: Process-scoped isolation vs. system-wide machine sampling on short-lived and fine-grained computing tasks.

---

## 1. Experimental Environment & Hardware Fingerprint

To guarantee strict scientific reproducibility, the experiment captured hardware telemetry and package versions via `EnvironmentSnapshot`:

| Property | Value |
| :--- | :--- |
| **CPU Architecture** | AMD64 (x86_64) |
| **Processor Model** | 13th Gen Intel(R) Core(TM) i7-13700H @ 2.92 GHz |
| **Physical / Logical Cores** | 14 Physical / 20 Logical Cores |
| **Installed RAM** | 15.65 GB (5.35 GB Available) |
| **Operating System** | Microsoft Windows 10 / 11 Enterprise (Build 26200) |
| **Python Runtime** | CPython 3.11.1 (64-bit) |
| **EcoTrace Version** | v1.6.0 |
| **CodeCarbon Version** | v3.3.1 |
| **Repetitions ($N$)** | 3 Measured Runs + Inter-Run Thermal Cooldown (0.5s) |

---

## 2. Empirical Results & Performance Matrix

Measurements compare **Zero-Instrumentation Baseline**, **EcoTrace (Process-Scoped 50ms)**, and **CodeCarbon (OfflineTracker 15s)**:

| Metric | Baseline (Unmetered) | EcoTrace (Continuous 50ms) | CodeCarbon (Default 15s) | Delta (EcoTrace vs. CodeCarbon) |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Execution Time** | **0.1247 s** | **0.1910 s** | **2.0319 s** | **10.6× faster execution** |
| **Execution Overhead** | — | **+53.13%** | **+1,529.26%** | **28.8× lower overhead** |
| **Sampling Interval** | — | **50 ms** | **15,000 ms (15s)** | **300× higher temporal resolution** |
| **Isolation Scope** | — | **Process-Scoped** | **System-Wide** | Eliminates multi-tenant noise |
| **Reported Carbon** | — | **0.004387 $gCO_2$** | **0.001033 $gCO_2$** | **4.25× discrepancy** (Temporal Aliasing) |

```
Execution Duration Comparison (Seconds - Lower is Better):
Baseline      [==] 0.125s
EcoTrace      [===] 0.191s (+0.066s)
CodeCarbon    [==============================================] 2.032s (+1.907s)
```

---

## 3. In-Depth Metrological Findings

### A. The Observer Effect & Architectural Trade-offs
* **CodeCarbon Architecture (+1,529% Relative Overhead on Sub-Second Tasks):** CodeCarbon is primarily architected for long-running batch and deep learning model training workloads spanning hours or days. In such multi-hour environments, a ~1.9s thread initialization and hardware probing routine represents a completely negligible (<0.001%) fraction of the total execution time. However, for sub-second workloads (such as microservices, serverless lambdas, and iterative unit benchmarks), this initialization phase accounts for the majority of observed runtime.
* **EcoTrace Architecture (+53% Overhead on Sub-Second Tasks):** EcoTrace is specifically engineered for low-latency lifecycle execution, employing a minimal polling daemon that begins and ends tracking in under 70ms of overhead, making it well-suited for fine-grained functions, continuous integration, and rapid iterations.

### B. Temporal Resolution & Sampling Aliasing (The 4.25× Discrepancy)
* **Ground Truth Note:** In the absence of an external physical hardware wattmeter (e.g., in-line power analyzer), software-level estimation libraries cannot claim absolute empirical ground truth on Windows where hardware RAPL counters are inaccessible.
* **Temporal Aliasing Analysis:** The 4.25× divergence between EcoTrace (0.00439 $gCO_2$) and CodeCarbon (0.00103 $gCO_2$) is explained by signal sampling mechanics:
  * CodeCarbon's default polling frequency is **15 seconds** (`measure_power_secs=15`).
  * When a workload executes in **0.125 seconds**, a 15-second interval violates the Nyquist-Shannon sampling requirement. The tracker captures essentially boundary idle snapshots, heavily diluting the active computational burst across its coarse time window.
  * EcoTrace's **50 ms** sampling frequency captures multiple discrete utilization points across the active burst, integrating the actual dynamic load curve rather than relying on sparse boundary estimates.

### C. Process-Level Isolation vs. System-Wide Multi-Tenancy
* **EcoTrace**: Measures `psutil.Process(pid).cpu_percent()` strictly for the target Python process hierarchy.
* **CodeCarbon**: Samples global machine power. On shared servers, multi-tenant Kubernetes clusters, or workstations running background tasks, system-wide sampling introduces noisy neighbor pollution into the reported carbon footprint.

---

## 4. Reproducibility & Benchmark Command

To reproduce these findings on your local workstation:

```bash
# 1. Install dependencies
pip install ecotrace codecarbon psutil

# 2. Run the empirical benchmark
python benchmarks/08_ecotrace_vs_codecarbon.py

# 3. View the generated JSON data
cat benchmarks/results/08_ecotrace_vs_codecarbon.json
```

---

## 5. Architectural Recommendations

1. **For Microservices, Lambda / Serverless & CI/CD Pipelines:** Use **EcoTrace** because sub-second latency overhead and rapid teardown are essential.
2. **For High-Frequency Profiling (< 1 minute runs):** High sampling frequencies ($\le 100\text{ ms}$) are necessary to avoid severe under-reporting caused by coarse 15-second windows.
3. **For Multi-Tenant & Shared Cloud Instances:** Process-level attribution is mandatory to prevent collateral energy pollution from neighboring containers.
