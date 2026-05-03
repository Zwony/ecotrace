<div align="center">

<img src="logo.png" width="200" alt="EcoTrace Logo">

# EcoTrace

### High-Precision Energy and Emissions Instrumentation
---
**Upcoming: v1.0.1 — Stable Release Target.** Previewing carbon budget enforcement, CI/CD gate, differential tracking, and session summaries.
---

**EcoTrace is a lightweight library for granular carbon footprint measurement of Python applications. No configuration files, no background services—just real-time hardware-level transparency.**

Real-time monitoring | 50+ Global Zones | AI-powered insights | Zero-configuration

<br>

[![PyPI - Version](https://img.shields.io/pypi/v/ecotrace.svg?color=2E8B57&style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ecotrace/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pepy/dt/ecotrace?style=for-the-badge&color=blue&logo=pypi&logoColor=white)](https://pepy.tech/project/ecotrace)
[![VS Code Extension](https://img.shields.io/badge/VS_Code-EcoTrace-007ACC?style=for-the-badge&logo=visual-studio-code)](https://marketplace.visualstudio.com/items?itemName=ecotrace-team.ecotrace-monitor)

<br>

> [!TIP]
> **VS Code Extension:** Monitor application carbon footprint in real-time during development. [Download here](https://marketplace.visualstudio.com/items?itemName=ecotrace-team.ecotrace-monitor).

<br>

![EcoTrace Demo](demo.gif)

*Function-level carbon measurement with real-time monitoring*

</div>

---

## Preview: What's Coming in v1.0.1

> **EcoTrace is heading towards Production/Stable.** The upcoming v1.0.1 release introduces active carbon budget enforcement — shifting from just measuring to active enforcement.

- **Carbon Budget Enforcement** — Set `carbon_limit` and get real-time alerts at 80% and 100% thresholds, with optional callback hooks.
- **CI/CD Carbon Gate** — `ecotrace gate --budget 10.0` returns exit code 1 if budget exceeded. No competitor has this.
- **Differential Tracking** — OS idle noise is now subtracted from measurements. You see only YOUR code's carbon cost.
- **Session Summary** — Automatic summary table at process exit: duration, functions tracked, total carbon, budget status.
- **Carbon Equivalences** — Abstract gCO2 values converted to relatable comparisons (Google searches, LED bulb time, car km).
- **Critical Bug Fixes** — Exception handling, GPU crash fixes, and packaging corrections. See [CHANGELOG.md](CHANGELOG.md).

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

### Option 1: Zero-Code Profiling (CLI)
Measure any script without changing a single line of code:

```bash
ecotrace run my_script.py
```

### Option 2: Programmatic Tracking (Library)
Decorate functions for granular instrumentation:

```python
from ecotrace import EcoTrace

eco = EcoTrace(region_code="US")

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

Enforce carbon budgets in your pipeline with a single command:

```yaml
# .github/workflows/ci.yml
- name: Run tests
  run: python -m pytest tests/

- name: Carbon Gate
  run: ecotrace gate --budget 10.0
```

If total emissions exceed the budget, the gate fails with exit code 1 — preventing carbon-heavy code from being merged.

---

## Why EcoTrace?

| Feature | **EcoTrace v1.0** | CodeCarbon | CarbonTracker |
|---|:---:|:---:|:---:|
| **Sampling Interval** | **50ms** | 15s | Per Epoch |
| **Isolation** | **Process-scoped** | System-wide | System-wide |
| **Budget Enforcement** | **Built-in** | No | No |
| **CI/CD Gate** | **Built-in** | No | No |
| **Idle Noise Subtraction** | **Automatic** | No | No |
| **Async Support** | **Native** | Limited | No |

- **Deep Transparency:** Derived from verified manufacturer TDP specifications rather than category averages.
- **Fail-Safe Architecture:** Guaranteed application continuity even if hardware drivers or API keys are missing.
- **Actionable AI:** Integrates with Google Gemini to provide specific code optimization advice (optional).

---

## Documentation

- [**Architecture and Science**](docs/ARCHITECTURE.md) — How the energy model and process isolation work.
- [**Advanced Usage**](docs/USAGE.md) — GPU tracking, AI insights, benchmarks, and comparison tables.
- [**Support and Reference**](docs/SUPPORT.md) — Troubleshooting, region codes, and hardware compatibility.

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