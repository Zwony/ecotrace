![EcoTrace Logo](images/logo.png)
# EcoTrace

### High-Precision Energy and Emissions Instrumentation
---
**v1.6.0 — Multi-GPU Continuous Tracking & Telemetry Resilience.** Multi-GPU power aggregation, DDR3 RAM hardware detection, persistent offline disk retry queue for `CloudExporter`, and strict static type safety overhaul.
---

**EcoTrace is a lightweight library for granular carbon footprint measurement of Python applications. No configuration files, no background services—just real-time hardware-level transparency.**

Real-time monitoring | 50+ Global Zones | AI-powered insights | Zero-configuration

<br>

[![Official Website](https://img.shields.io/badge/Website-ecotracelibrary.com-2E8B57?style=for-the-badge&logo=google-chrome&logoColor=white)](https://ecotracelibrary.com)
[![PyPI - Version](https://img.shields.io/pypi/v/ecotrace.svg?color=2E8B57&style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ecotrace/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pepy/dt/ecotrace?style=for-the-badge&color=blue&logo=pypi&logoColor=white)](https://pepy.tech/project/ecotrace)
[![VS Code Extension](https://img.shields.io/badge/VS_Code-EcoTrace-007ACC?style=for-the-badge&logo=visual-studio-code)](https://marketplace.visualstudio.com/items?itemName=ecotrace-team.ecotrace-monitor)

<br>

> [!TIP]
> 🌐 **Live Web Observatory:** Stream and monitor your application carbon footprint in real-time on our hosted web platform at [**ecotracelibrary.com**](https://ecotracelibrary.com).

> [!TIP]
> **VS Code Extension:** Monitor application carbon footprint in real-time during development. [Download here](https://marketplace.visualstudio.com/items?itemName=ecotrace-team.ecotrace-monitor).

<br>

![EcoTrace Demo](images/demo.gif)

*Function-level carbon measurement with real-time monitoring*

---

## Core Features in v1.6.0

> **Latest Release.** v1.6.0 introduces automated multi-GPU continuous power tracking, DDR3 RAM hardware detection, a persistent offline disk retry queue for cloud telemetry, and a comprehensive type safety overhaul.

- **Automated Multi-GPU Tracking & Aggregation (`ecotrace.gpu`)** — Automatically discovers all available NVIDIA GPUs via NVML (`get_all_gpu_info`) and aggregates instantaneous power draw at 50ms intervals across active accelerators (`get_all_gpu_power_w`).
- **Comprehensive Multi-Device Telemetry** — Startup logs, session summaries, and exported JSON/CSV artifacts now report full GPU array metadata (total GPU count, device models, and combined TDP limit).
- **Offline Disk Retry Queue (`CloudExporter`)** — Telemetry payloads are safely persisted to an isolated local disk queue (`~/.ecotrace/retry_queue`) during network outages or backend 5xx errors, automatically flushing in chronological FIFO order (up to 50 entries) upon reconnection.
- **DDR3 RAM Speed Detection (`ecotrace.ram`)** — Evaluates memory clock frequencies (800–2133 MHz) via Linux `dmidecode` and Windows WMI, applying calibrated DDR3 power factors (0.500 W/GB) for accurate carbon accounting on legacy enterprise hardware.
- **Strict Static Type Safety & Diagnostics Overhaul** — Complete overhaul eliminating `# type: ignore` workarounds across `core.py`, `gpu.py`, and exporters, achieving clean IDE diagnostics under Pyright/Pylance and hardened exception handling.
- **Unified Multi-Device Architecture** — Deprecates single-device `gpu_index` targeting in favor of unified multi-accelerator tracking, emitting a backward-compatible `DeprecationWarning` if `gpu_index > 0` is passed.

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
  uses: Zwony/ecotrace@v1.6.0
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

| Feature | **EcoTrace v1.6** | CodeCarbon | CarbonTracker |
|---|:---:|:---:|:---:|
| **Sampling Interval** | **50ms** | 15s | Per Epoch |
| **Isolation** | **Process-scoped** | System-wide | System-wide |
| **Cloud Dashboard Sync** | **Native** | No | No |
| **Multi-GPU Tracking** | **Continuous (Aggregated)** | Single GPU | Per Epoch |
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

- [**Official Website**](https://ecotracelibrary.com) — Live carbon dashboard and web management platform.
- [**Architecture and Science**](ARCHITECTURE.md) — How the energy model and process isolation work.
- [**Advanced Usage**](USAGE.md) — GPU tracking, AI insights, benchmarks, and comparison tables.
- [**Support and Reference**](SUPPORT.md) — Troubleshooting, region codes, and hardware compatibility.

---

## Contributing

We welcome contributions! Please see our [**CONTRIBUTING.MD**](CONTRIBUTING.MD) for guidelines on reporting bugs, suggesting features, or contributing hardware data.

---

## Community

[![Join Discord](https://img.shields.io/badge/Discord-Join%20Community-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/hs58XXb3Uq)

[CHANGELOG.md](CHANGELOG.md) · [SECURITY.MD](SECURITY.MD)

---

## Author and License

**Emre Ozkal** — [GitHub](https://github.com/Zwony) · [ecotraceteam@gmail.com](mailto:ecotraceteam@gmail.com)

MIT License — Use it however you like.

*Developed for sustainable software development practices.*
