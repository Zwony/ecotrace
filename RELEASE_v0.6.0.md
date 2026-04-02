# 🌍 EcoTrace v0.6.0 — The Sustainability OS Update

**Release Date:** 01.04.2026
**Version:** v0.6.0  
**Focus:** Live Grid API Integration & Auto-Update System

---

## 🌟 What's New

### 🌍 Live Grid API (Electricity Maps Integration)
EcoTrace v0.6.0 officially moves from static averages to **real-time carbon intensity data**.
- **Real-Time Data:** Measures your footprint based on the *actual* energy mix at the exact moment your code runs.
- **38 Global Zones:** Completely mapped to Electricity Maps regions.
- **Intelligent Caching:** 1-hour in-memory cache to prevent unnecessary network requests and respect API rate limits.
- **Zero-Impact Fallback:** No API key? No internet? Seamlessly falls back to our robust static constant mapping without crashing.

### 📍 Automatic Region Detection (IP-Based)
EcoTrace now intelligently identifies your location to provide the most accurate default data possible.
- **Smart Defaults:** If no `region_code` is provided, the engine uses your IP address to detect your country and match it against our carbon intensity database.
- **Universal Scope:** The default region has been moved from `"TR"` (Turkey) to `"GLOBAL"`, ensuring a more inclusive out-of-the-box experience for international users.
- **Privacy Conscious:** Uses lightweight, public IP-API lookups with sub-second response times and zero persistent tracking.

### 📍 Expanded Global Coverage
We've significantly grown our supported regions to include critical global technology and data center hubs.
- **50+ Strategic Regions:** Now includes precise mapping for **Ireland (IE)**, **Israel (IL)**, **Taiwan (TW)**, **UAE (AE)**, **Colombia (CO)**, and more.
- **Tech-Hub Ready:** Accurate default tracking for the world's most dense developer regions, ensuring minimal error for major cloud deployments.

### 🌱 Interactive Auto-Update System
Stay on top of algorithmic improvements and database updates.
- **Startup Check:** Non-blocking 3-second check for new PyPI versions.
- **Interactive Upgrade:** Prompts you gracefully in the terminal ("Would you like to update EcoTrace? (y/n)") and runs the pip upgrade without disrupting the workflow.
- **CI/CD Safe:** Automatically skips the update block in non-interactive pipeline environments or when explicitly disabled (`check_updates=False`).

### ⚙️ Engine Refinements
- **Refined Developer Experience (DX):** Replaced the basic initialization log with a **High-End Minimalist Banner** featuring icons and detailed hardware profiling.
- **Quiet Mode:** Added support for `EcoTrace(quiet=True)` to completely silence all standard output—ideal for production logs and clean CLI tool integration.
- **Test Infrastructure:** Added a robust test suite (`test_v6_features.py`) with full mock integration for network failure and API stress testing.
- **Docstring Polish:** All new functions and public APIs are documented under the rigorous Google Style standard.

---

## 🛠️ Backward Compatibility
- **100% Core Compatibility:** Existing code continues to work without modification.
- **Default Change:** Users who previously relied on the implicit `"TR"` default now receive a more accurate global average or auto-detected local region.

---

## 🚀 How to Upgrade
```bash
pip install --upgrade ecotrace
```

*From a measurement tool to a full Sustainability Operating System.*
