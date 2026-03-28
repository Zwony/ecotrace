# 🚀 EcoTrace v0.5.0 — The Hardware Intelligence Update

**Release Date:** 28.03.2026 (Released 1 Day Early!)  
**Version:** v0.5.0  
**Focus:** High-Precision Hardware Analysis & AI-Powered Sustainability Insights

---

## 🌟 Major Features

### 1. 🧬 Smart Core Normalization
Developed a core-aware utilization tracking system that properly scales across multi-core processors (1 to 128+ logical cores). This eliminates the "inflation" effect in multi-threaded Python applications, providing scientific accuracy for real-world production workloads.

### 2. ⚡ RAM Generation Tracking
Introducing deep RAM analysis. EcoTrace now detects RAM type (DDR4, DDR5, LPDDR) and MHz speed to apply specific watt-factors (RSS-based recursive process tracking), making energy estimation for data-heavy tasks significantly more accurate.

### 3. 🤖 Gemini AI Insights (Beta)
The highlight of this release. EcoTrace now optionally integrates with **Google Gemini AI**. Instead of static alerts, developers get:
- **Hardware-Aware Optimization**: Recommendations tailored to your specific CPU/GPU model.
- **Pythonic Green Refactoring**: Suggestions for async, vectorization, or library-level swaps to reduce carbon spikes.
- **Actionable Sustainability**: "Green coding" advice directly in your audit-ready PDF reports.

### 🍎 Apple Silicon Optimization
Full native support for M1, M2, and M3 series architectures, including specific power profile mappings for Mac users.

---

## 🛠️ Architectural Improvements
- **Deep Modularization**: Refactored the engine into distinct `cpu`, `gpu`, and `ram` intelligence modules.
- **Stability Core**: Hardened the monitoring daemon to ensure zero impact on production performance.
- **Strict Input Validation**: 100% Google-style docstrings and strict verification for `gpu_index` and `region_code`.

---

## 🚀 How to Upgrade
```bash
pip install --upgrade ecotrace
```

*Built with 💚 for a sustainable software future.*
