# EcoTrace v0.5.0 Release Notes
**The Hardware Intelligence Update** 🚀

We are incredibly excited to announce the release of **v0.5.0**, a monumental leap forward in EcoTrace's evolution from a simple script into a robust, enterprise-grade, highly modular carbon tracking framework.

## 🌟 Major Highlights

### 1. Enterprise Modularization
EcoTrace `core.py` has been systematically decoupled into focused, decoupled intelligence modules:
- `cpu.py`: Centralizes py-cpuinfo caching, Boavizta CPU JSON lookup logic, and fuzzy matching calculations.
- `gpu.py`: Handles multi-vendor GPU parsing (NVIDIA NVML & Windows WMI) transparently preventing any runtime crashing.
- `ram.py`: Deploys OS-native subprocesses (`wmic`/`dmidecode`) evaluating live DDR4/DDR5 memory bandwidth and estimating power scaling safely.
- `config.py`: Acts as the secure bridge validating ISO Region codes and assigning ISO-calibrated carbon intensities.
- `report.py`: Injects AI diagnostics and handles the heavy Matplotlib charts without clogging memory bounds.

### 2. Smart Core Normalization
Older iterations of tracking blindly accumulated 100% CPU utilization across any Python thread. v0.5.0 analyzes your underlying hardware topology and perfectly normalizes high-stress CPU threads against all logical cores accurately modeling actual Socket Power drain.

### 3. Apple Silicon Overhaul
Fully mapped the M1, M2, M3, and M4 chipset family boundaries directly mapping to accurate laptop-board specific 25.0W defaults seamlessly integrated strictly relying on our JSON schema. 

### 4. Exception Guard Resilience
Added strict `try...finally` boundaries to all active tracking decorators! If your measured method crashes and dumps, EcoTrace will guarantee that the prior executed power utilization gets correctly calculated, exported, and cleanly joined against your existing traces.

## 🛠️ Deprecations & Maintenance
- Swapped every piece of inline developer comments for professional, strict Google-style Docstrings across all functions.
- Pushed `.__version__` exposures structurally enforcing standard PEP packaging practices.

**Available now via PyPI.** Run `pip install --upgrade ecotrace` to harness the most scientifically profound software-tracking mechanism!
