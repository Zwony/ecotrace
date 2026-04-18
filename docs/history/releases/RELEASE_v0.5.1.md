# 🚀 EcoTrace v0.5.1 — The Precision & Reporting Patch

**Release Date:** 28.03.2026 (Rapid Response Update)  
**Version:** v0.5.1  
**Focus:** Visual Analytics Restoration & Smart Insight Logic

---

## 🌟 What's New

### 📈 Automated PDF Visuals
Fixed a regression where CPU/GPU charts were omitted in v0.5.0 reports unless manually passed. 
- **Auto-Snapshoting**: `generate_pdf_report()` now automatically captures the entire session's monitoring data for high-resolution utilization graphs.
- **GPU Visualization**: Restored and improved the GPU utilization chart (SteelBlue theme) for NVIDIA, AMD, and Intel hardware.

### 🧠 Balanced Performance Insights
Refined the internal recommendation engine to account for **Smart Core Normalization**. 
- **Dynamic Thresholds**: Optimization advice now scales based on the system's core count, eliminating false-positive "Try batching" warnings for single-threaded tasks on high-core processors (e.g., Apple M3 or Intel i9).
- **New Terminology**: Realistically distinguishes between "Single-Thread Intensive" tasks and true "High Multi-Core" system-wide stress.

### 🛡️ Hardware Robustness
Improved GPU detection logic for Intel Iris Xe and AMD integrated graphics, ensuring monitoring threads initialize correctly across all vendor classes.

---

## 🛠️ Internal Improvements
- **Thread-Safe Reporting**: Snapshotting internal deques for PDF generation is now protected by monitoring locks.
- **CSV Data Consistency**: Fixed historical log parsing in the PDF generator to match the new v0.5.1 multi-column format.
- **Optimized Heuristics**: Prioritized execution-time alerts over utilization flags for actionable "Green Coding" advice.

---

## 🚀 How to Upgrade
```bash
pip install --upgrade ecotrace
```

*Rapidly refined for a more transparent and accurate sustainability future.*
