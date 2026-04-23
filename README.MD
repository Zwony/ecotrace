<div align="center">

<img src="logo.png" width="200" alt="EcoTrace Logo">

# EcoTrace

### High-Precision Energy and Emissions Instrumentation

**EcoTrace is a lightweight library for granular carbon footprint measurement of Python applications. No configuration files, no background services—just real-time hardware-level transparency.**

Real-time monitoring · 50+ Global Zones · AI-powered insights · Zero-configuration

<br>

[![PyPI - Version](https://img.shields.io/pypi/v/ecotrace.svg?color=2E8B57&style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ecotrace/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pepy/dt/ecotrace?style=for-the-badge&color=blue&logo=pypi&logoColor=white)](https://pepy.tech/project/ecotrace)
[![VS Code Extension](https://img.shields.io/badge/VS_Code-EcoTrace-007ACC?style=for-the-badge&logo=visual-studio-code)](https://marketplace.visualstudio.com/items?itemName=ecotrace-team.ecotrace-monitor)

<br>

> [!IMPORTANT]
> **Upcoming Release (April 24, 2026):** EcoTrace v0.8.0 "Ecosystem Release" is arriving tomorrow. This major update introduces the new EcoTrace CLI, structured JSON export capabilities, and zero-configuration profiling for any Python script.

<br>

> [!TIP]
> **VS Code Extension:** Monitor application carbon footprint in real-time during development. [Download here](https://marketplace.visualstudio.com/items?itemName=ecotrace-team.ecotrace-monitor).

<br>

![EcoTrace Demo](demo.gif)

*Function-level carbon measurement with real-time monitoring*

</div>

---

## Quick Install

```bash
pip install ecotrace
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
eco.generate_pdf_report("report.pdf")
```

---

## Why EcoTrace?

*   **Continuous 50ms Sampling:** Captures bursts that 15-second trackers miss.
*   **Process Isolation:** Only measures your code, filtered from OS background noise.
*   **Zero Dependencies:** Core measurement engine uses only Python standard library.
*   **Tri-Vendor GPU:** Real-time TDP tracking for NVIDIA, AMD, and Intel.

---

## Documentation

Detailed information is available in the following guides:

- [**Architecture and Science**](docs/ARCHITECTURE.md) — How the energy model and process isolation work.
- [**Advanced Usage**](docs/USAGE.md) — GPU tracking, AI insights, benchmarks, and comparison tables.
- [**Support and Reference**](docs/SUPPORT.md) — Troubleshooting, region codes, and hardware compatibility.

---

## Community

[![Join Discord](https://img.shields.io/discord/1483105790993633411?label=Join%20Community&logo=discord&style=for-the-badge&color=5865F2)](https://discord.gg/hs58XXb3Uq)

Report bugs · Suggest features · Contribute TDP data · [CHANGELOG.md](CHANGELOG.md)

---

## Author and License

**Emre Ozkal** — [GitHub](https://github.com/Zwony) · [ecotraceteam@gmail.com](mailto:ecotraceteam@gmail.com)

MIT License — Use it however you like.

<div align="center">

*Developed for sustainable software development practices.*

</div>