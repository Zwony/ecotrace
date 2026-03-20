# 🌱 EcoTrace v1.0.0 — First Stable Release

> Measure your code's carbon footprint. Write cleaner code. Protect the planet.

After **3,000+ downloads** in the first days, EcoTrace is officially hitting its first stable release. Thank you to everyone who tried it, cloned it, and gave feedback. 🙏

---

## ✨ What's in v1.0.0

### Core Features
- **`@eco.track`** — Decorator to measure CPU load and CO₂ emission of any function
- **`@eco.track_gpu`** — GPU tracking with NVIDIA, AMD, and Intel support
- **`eco.measure_async()`** — Accurate continuous sampling for async functions
- **`eco.compare()`** — Side-by-side carbon comparison of two implementations
- **`eco.generate_pdf_report()`** — Full PDF report with CPU usage charts

### Platform Support
- ✅ Windows, Linux, macOS
- ✅ Python 3.7+
- ✅ NVIDIA / AMD / Intel GPU support
- ✅ 1800+ CPUs via Boavizta database
- ✅ Automatic TDP detection with smart fallback

### Supported Regions
| Code | Country | Carbon Intensity |
|------|---------|-----------------|
| TR | Turkey | 475 gCO₂/kWh |
| DE | Germany | 385 gCO₂/kWh |
| FR | France | 55 gCO₂/kWh |
| US | United States | 367 gCO₂/kWh |
| GB | United Kingdom | 253 gCO₂/kWh |

---

## 🚀 Getting Started

```bash
pip install ecotrace
```

```python
from ecotrace import EcoTrace

eco = EcoTrace(region_code="US")

@eco.track
def my_function():
    return sum(i * i for i in range(10**6))

my_function()
# [EcoTrace] CO2 Emitted: 0.00001823 gCO2
```

---

## 💬 Community

- 🐛 Found a bug? [Open an issue](https://github.com/Zwony/ecotrace/issues/new?template=bug_report.md)
- 💡 Have an idea? [Request a feature](https://github.com/Zwony/ecotrace/issues/new?template=feature_request.md)
- 💬 Join us on [Discord](https://discord.gg/hs58XXb3Uq)

---

**Full Changelog**: https://github.com/Zwony/ecotrace/commits/main