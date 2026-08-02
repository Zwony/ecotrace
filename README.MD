<div align="center">

<img src="assets/logo.png" width="200" alt="EcoTrace Logo">

# EcoTrace

### High-Precision Energy and Emissions Instrumentation
---
**v1.5.0 — Hosted Cloud Integration & Real-Time Observatory.** Native `CloudExporter`, terminal authentication (`ecotrace login`), 6,980+ CPU TDP database, Python 3.14+ readiness, WebSocket live streaming, and session run filtering.
---

**EcoTrace is a lightweight library for granular carbon footprint measurement of Python applications. No configuration files, no background services—just real-time hardware-level transparency.**

Real-time monitoring | 50+ Global Zones | AI-powered insights | Zero-configuration

<br>

[![Official Website](https://img.shields.io/badge/Website-ecotracelibrary.com-2E8B57?style=for-the-badge&logo=google-chrome&logoColor=white)](https://ecotracelibrary.com)
[![PyPI - Version](https://img.shields.io/pypi/v/ecotrace.svg?color=2E8B57&style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ecotrace/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pepy/dt/ecotrace?style=for-the-badge&color=blue&logo=pypi&logoColor=white)](https://pepy.tech/project/ecotrace)
[![Join Discord](https://img.shields.io/discord/1483105790993633411?label=Join%20Community&logo=discord&style=for-the-badge&color=5865F2)](https://discord.gg/hs58XXb3Uq)
[![VS Code Extension](https://img.shields.io/badge/VS_Code-EcoTrace-007ACC?style=for-the-badge&logo=visual-studio-code)](https://marketplace.visualstudio.com/items?itemName=ecotrace-team.ecotrace-monitor)

<br>

> [!TIP]
>  **Live Web Observatory:** Stream and monitor your application carbon footprint in real-time on our hosted web platform at [**ecotracelibrary.com**](https://ecotracelibrary.com).

> [!TIP]
> **VS Code Extension:** Monitor application carbon footprint in real-time during development. [Download here](https://marketplace.visualstudio.com/items?itemName=ecotrace-team.ecotrace-monitor).

<br>

![EcoTrace Demo](assets/demo.gif)

*Function-level carbon measurement with real-time monitoring*

</div>

---

## Core Features in v1.5.0

> **Major Release.** v1.5.0 introduces direct cloud telemetry streaming to [ecotracelibrary.com](https://ecotracelibrary.com), terminal authentication (`ecotrace login`), 6,980+ CPU TDP database coverage, Python 3.14+ compatibility, and WebSocket live streaming.

-  **Hosted Cloud Observatory (`CloudExporter`)** — Stream carbon metrics directly to your private web dashboard on [ecotracelibrary.com](https://ecotracelibrary.com) using `EcoTrace(api_key="eco_usr_...")`.
-  **CLI Credential Management (`ecotrace login`)** — Authenticate your terminal once via `ecotrace login --key eco_usr_...` so all `ecotrace run` profiling runs automatically stream to your web dashboard.
-  **6,980+ CPU TDP Database (%100 TDP Validity)** — Expanded dataset from 1,806 to 6,983 unique CPU models, including +760% mobile/laptop CPU coverage (Intel 10th-14th Gen, Core Ultra, AMD Ryzen, Apple Silicon M1-M4).
-  **Python 3.8 → 3.14+ Compatibility** — Fully verified runtime compatibility across Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, and 3.14+.
-  **WebSocket Real-Time Streaming** — Instant live metric updates on your web dashboard via `/api/ws/live`.
-  **Session Run Filtering** — Filter web dashboard metrics by specific `run_id` / `run_label` execution sessions.
-  **Pausing API** — Temporarily disable carbon tracking using `EcoTrace.pause()` and `EcoTrace.resume()`.
-  **Run Comparisons (`ecotrace diff`)** — Perform side-by-side carbon and duration comparisons between runs.

---

## Quick Install

```bash
pip install ecotrace
```

Optional extras:
```bash
pip install ecotrace[gpu]   # NVIDIA GPU support
pip install ecotrace[ai]    # Gemini AI insights
pip install ecotrace[all]   # Everything
```

---

## Quick Start

### Option 1: Zero-Code Profiling (CLI + Cloud Sync)
Authenticate your terminal once, then profile any script without changing source code:

```bash
# 1. Login with your ingestion key from https://ecotracelibrary.com
ecotrace login --key eco_usr_abc123...

# 2. Run your script — metrics automatically stream to your web dashboard!
ecotrace run my_script.py
```

### Option 2: Programmatic Tracking & Cloud Dashboard
Decorate functions for granular instrumentation and stream metrics to your web account:

```python
from ecotrace import EcoTrace

# Connects directly to your hosted account at https://ecotracelibrary.com
eco = EcoTrace(api_key="eco_usr_abc123...", region_code="US")

@eco.track
def my_function():
    # Your heavy processing here
    pass

my_function()

# Export audit-ready reports or check cumulative totals
eco.generate_pdf_report("carbon_audit.pdf")
print(f"Total Carbon Emitted: {eco.total_carbon} gCO2")
```

### Option 3: Carbon Budget Mode
Set a limit and let EcoTrace enforce it:

```python
eco = EcoTrace(
    region_code="TR",
    carbon_limit=5.0,                   # 5 gCO2 budget
    on_budget_exceeded=lambda t, l: print(f"Budget exceeded: {t:.4f}/{l:.4f} gCO2")
)

@eco.track
def training_pipeline():
    ...

training_pipeline()
print(f"Remaining budget: {eco.remaining_budget} gCO2")
```

### Expected Output
When initialized, EcoTrace performs automated hardware detection:

```text
[EcoTrace] INFO: [INFO] EcoTrace instrumentation session initialized (STATIC).
[EcoTrace] INFO: -----------------------------------------------------
[EcoTrace] INFO: Region        : TR (475 gCO2/kWh)
[EcoTrace] INFO: Hardware Logic: 13th Gen Intel Core i7-13700H
[EcoTrace] INFO: Specifications: 20 Cores | 45.0W TDP
[EcoTrace] INFO: Energy Sensor : Boavizta Advanced Estimation
[EcoTrace] INFO: Memory Config : 15.6 GB DDR4
[EcoTrace] INFO: GPU Accelerator: Intel Iris Xe Graphics (15.0W TDP)
[EcoTrace] INFO: -----------------------------------------------------
```

At process exit, a session summary is printed automatically:

```text
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

---

## CI/CD Integration

### Official GitHub Action
Enforce carbon budgets in your pipeline with our official GitHub Action. Add this to your `.github/workflows/ci.yml`:

```yaml
- name: EcoTrace Carbon Gate
  uses: Zwony/ecotrace@v1.5.0
  with:
    budget: '10.0'
    region: 'US'
```

### Manual CLI Integration
You can also run the gate manually:
```bash
ecotrace gate --budget 10.0
```

If total emissions exceed the budget, the gate fails with exit code 1 — preventing carbon-heavy code from being merged.

---

## Why EcoTrace?

| Feature | **EcoTrace v1.5** | CodeCarbon | CarbonTracker |
|---|:---:|:---:|:---:|
| **Sampling Interval** | **50ms** | 15s | Per Epoch |
| **Isolation** | **Process-scoped** | System-wide | System-wide |
| **Cloud Dashboard Sync** | **Native** | No | No |
| **CPU Dataset** | **6,980+ CPUs** | Limited | Limited |
| **Budget Enforcement** | **Built-in** | No | No |
| **CI/CD Gate** | **Built-in** | No | No |
| **Idle Noise Subtraction** | **Automatic** | No | No |
| **Async Support** | **Native** | Limited | No |

- **Deep Transparency:** Derived from 6,980+ verified manufacturer TDP specifications rather than category averages.
- **Fail-Safe Architecture:** Guaranteed application continuity even if hardware drivers or API keys are missing.
- **Actionable AI:** Integrates with Google Gemini to provide specific code optimization advice (optional).

---

## Documentation

Full documentation is available at [**ecotracelibrary.com**](https://ecotracelibrary.com) and [**ecotrace.readthedocs.io**](https://ecotrace.readthedocs.io/en/latest/).

- [**Official Website**](https://ecotracelibrary.com) — Live carbon dashboard and web management platform.
- [**Architecture and Science**](https://ecotrace.readthedocs.io/en/latest/ARCHITECTURE/) — How the energy model and process isolation work.
- [**Advanced Usage**](https://ecotrace.readthedocs.io/en/latest/USAGE/) — GPU tracking, AI insights, benchmarks, and comparison tables.
- [**API Reference**](https://ecotrace.readthedocs.io/en/latest/api/) — Technical documentation for core classes and functions.
- [**Support and Reference**](https://ecotrace.readthedocs.io/en/latest/SUPPORT/) — Troubleshooting, region codes, and hardware compatibility.

---

## Contributing

We welcome contributions! Please see our [**CONTRIBUTING.MD**](CONTRIBUTING.MD) for guidelines on reporting bugs, suggesting features, or contributing hardware data.

---

## Community

[![Join Discord](https://img.shields.io/discord/1483105790993633411?label=Join%20Community&logo=discord&style=for-the-badge&color=5865F2)](https://discord.gg/hs58XXb3Uq)

[CHANGELOG.md](CHANGELOG.md) · [SECURITY.MD](SECURITY.MD)

---

## Author and License

**Emre Ozkal** — [GitHub](https://github.com/Zwony) · [ecotraceteam@gmail.com](mailto:ecotraceteam@gmail.com)

MIT License — Use it however you like.

<div align="center">

*Developed for sustainable software development practices.*

</div>
