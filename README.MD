<div align="center">

<img src="assets/logo.png" width="200" alt="EcoTrace Logo">

# EcoTrace

### High-Precision Energy and Emissions Instrumentation
---
**v1.6.1 — HuggingFace Integration, CodeCarbon Drop-in API & Metrology Study.** Native HuggingFace Trainer callback, CodeCarbon-compatible API layer (`EmissionsTracker`), Case 08 Metrology & Overhead benchmark, and Zenodo DOI archival integration.
---

**EcoTrace is a lightweight library for granular carbon footprint measurement of Python applications. No configuration files, no background services—just real-time hardware-level transparency.**

Real-time monitoring | 50+ Global Zones | AI-powered insights | Zero-configuration

<br>

[![PyPI - Version](https://img.shields.io/pypi/v/ecotrace.svg?color=2E8B57&style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/ecotrace/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Downloads](https://img.shields.io/pepy/dt/ecotrace?style=flat-square&color=blue&logo=pypi&logoColor=white)](https://pepy.tech/project/ecotrace)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22834060.svg)](https://doi.org/10.5281/zenodo.22834060)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/Zwony/ecotrace/badge)](https://scorecard.dev/viewer/?uri=github.com/Zwony/ecotrace)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/14713/badge)](https://www.bestpractices.dev/projects/14713)
[![codecov](https://codecov.io/gh/Zwony/ecotrace/graph/badge.svg)](https://codecov.io/gh/Zwony/ecotrace)
[![Join Discord](https://img.shields.io/badge/Discord-Join%20Community-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discord.gg/hs58XXb3Uq)

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

## Core Features in v1.6.1

> **Latest Release.** v1.6.1 introduces native HuggingFace Trainer callbacks, drop-in CodeCarbon API compatibility, the Case 08 Observer Effect benchmark study, and official Zenodo DOI archival indexing.

- **HuggingFace Transformers Callback (`ecotrace.callbacks.huggingface`)** — Native `EcoTraceHuggingFaceCallback` injecting instantaneous power draw (W) and cumulative carbon metrics directly into `state.log_history` on step and epoch intervals.
- **CodeCarbon Drop-in API (`ecotrace.tracker`)** — Zero-codebase-refactoring drop-in replacement (`EmissionsTracker`, `OfflineEmissionsTracker`, `@track_emissions`) enabling existing projects to switch to EcoTrace seamlessly.
- **Automated Multi-GPU Tracking & Aggregation (`ecotrace.gpu`)** — Automatically discovers all available NVIDIA GPUs via NVML (`get_all_gpu_info`) and aggregates instantaneous power draw at 50ms intervals across active accelerators.
- **Offline Disk Retry Queue (`CloudExporter`)** — Telemetry payloads are safely persisted to an isolated local disk queue during network outages, automatically flushing in chronological FIFO order upon reconnection.
- **Zenodo DOI Archival Integration** — Standardized metadata (`.zenodo.json`, `CITATION.cff`) ensuring verifiable scientific citation and permanent preservation.

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

### Option 4: HuggingFace Transformers Integration
Log step-by-step carbon emissions automatically inside HuggingFace `Trainer`:

```python
from transformers import Trainer
from ecotrace.callbacks import EcoTraceHuggingFaceCallback

trainer = Trainer(
    model=model,
    args=training_args,
    callbacks=[EcoTraceHuggingFaceCallback()],
)
trainer.train()
```

### Option 5: Drop-in CodeCarbon Compatibility
Migrate legacy codebases with zero refactoring — just change your import:

```python
# from codecarbon import EmissionsTracker  <-- Change to EcoTrace:
from ecotrace import EmissionsTracker

tracker = EmissionsTracker(project_name="bert-finetuning")
tracker.start()
# ... your model training or inference ...
emissions = tracker.stop()
print(f"Emissions: {emissions:.6f} kg CO2")
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

## CI/CD & Testing Integration

### Official GitHub Action (Carbon Gate)
Enforce carbon emission budgets directly in your GitHub pull requests. Add this to your `.github/workflows/ci.yml`:

```yaml
- name: Run Tests with Carbon Profiling
  run: pytest --ecotrace

- name: EcoTrace Carbon Gate
  uses: Zwony/ecotrace@v1.6.1
  with:
    budget: '5.0'    # Fails pipeline if total test emissions exceed 5.0 gCO2
    region: 'US'
```

### Pytest Plugin Integration
Measure per-test function carbon footprints directly from your test suite:

```bash
pytest --ecotrace
```

### Manual CLI Gate
Run the gate locally or inside custom continuous integration pipelines:

```bash
ecotrace gate --budget 5.0 --region US
```

If total emissions recorded in `ecotrace_log.csv` exceed the budget, the command exits with code `1` — preventing carbon-heavy regressions from merging into production.

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

## Academic Benchmarks & Empirical Research

> [!TIP]
> 📄 **Official Technical Whitepaper:** Download the comprehensive [**EcoTrace Technical Whitepaper (PDF)**](EcoTrace_Whitepaper.pdf) or view the online [**WHITE_PAPER.md**](WHITE_PAPER.md) for complete mathematical derivations, RAPL hardware validation metrics ($MAPE \le 6.8\%$), and empirical study analyses.

EcoTrace includes a reproducible [**Academic Benchmark Suite**](benchmarks/) designed for peer-reviewed green computing research. Every article in `benchmarks/articles/` is **auto-generated** from real measurement JSONs in `benchmarks/results/` by `benchmarks/report_generator.py` — re-run the generator after new measurements to keep the published numbers in sync.

- **Data Engineering:** [Pandas vs. Polars on 5M Rows](benchmarks/articles/01_pandas_vs_polars.md) — 83.8% carbon reduction via Arrow vectorization (real numbers from this machine).
- **Computer Science:** [Algorithmic Complexity Carbon Scaling](benchmarks/articles/03_sorting_algorithms.md) — Insertion Sort at $N = 50{,}000$ emits **~3,469× more carbon** than NumPy on the same input (the *quadratic carbon cliff*).
- **Cloud Architecture:** [Web Framework Throughput vs. Carbon](benchmarks/articles/04_web_frameworks.md) — Flask vs. FastAPI under identical load; FastAPI achieves 1.13× speedup and 9.8% carbon reduction (CPU mode).
- **Generative AI:** [LLM Inference Carbon Footprint](benchmarks/articles/05_llm_inference.md) — Per-token energy and carbon cost of GPT-2 inference (CPU mode; medium/large models require GPU).
- **Cloud Architecture:** [Spatial Carbon Arbitrage across 15 Countries](benchmarks/articles/06_regional_carbon.md) — The same workload in South Africa emits **~73× more carbon** than in Sweden (a 99% reduction is achievable by region selection alone).
- **Metrology Validation:** [Empirical Accuracy vs. Intel RAPL Counters](benchmarks/articles/07_accuracy_validation.md) — model-vs-hardware validation methodology with honest synthetic-mode fallback for non-Linux systems.
- **Machine Learning:** [PyTorch vs. TensorFlow CNN Training](benchmarks/articles/02_ml_training_frameworks.md) — Carbon per accuracy point analysis (CPU mode; numbers regenerate after each run).

### Citing EcoTrace

If you use EcoTrace or its benchmark suite in scientific publications:

```bibtex
@software{ozkal2026ecotrace,
  author = {Ozkal, Emre},
  title = {EcoTrace: High-Precision Energy and Emissions Instrumentation for Python},
  year = {2026},
  url = {https://github.com/Zwony/ecotrace},
  version = {1.6.0}
}
```

---

## Documentation

Full documentation is available at [**ecotracelibrary.com**](https://ecotracelibrary.com) and [**ecotrace.readthedocs.io**](https://ecotrace.readthedocs.io/en/latest/).

- [**Official Website**](https://ecotracelibrary.com) — Live carbon dashboard and web management platform.
- [**Architecture and Science**](https://ecotrace.readthedocs.io/en/latest/ARCHITECTURE/) — How the energy model and process isolation work.
- [**Advanced Usage**](https://ecotrace.readthedocs.io/en/latest/USAGE/) — GPU tracking, AI insights, benchmarks, and comparison tables.
- [**API Reference**](https://ecotrace.readthedocs.io/en/latest/api/) — Technical documentation for core classes and functions.
- [**Support and Reference**](https://ecotrace.readthedocs.io/en/latest/SUPPORT/) — Troubleshooting, region codes, and hardware compatibility.
- [**Technical Whitepaper (PDF)**](EcoTrace_Whitepaper.pdf) — Comprehensive metrology and empirical evaluation report.

---

## Citation

If you use EcoTrace in academic research or sustainability audits, please cite:

```bibtex
@software{ecotrace2026,
  author = {Ozkal, Emre},
  title = {EcoTrace: High-Precision Energy and Emissions Instrumentation for Python},
  year = {2026},
  publisher = {Zenodo},
  version = {v1.6.1},
  doi = {10.5281/zenodo.22834060},
  url = {https://doi.org/10.5281/zenodo.22834060}
}
```

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

<div align="center">

*Developed for sustainable software development practices.*

</div>
