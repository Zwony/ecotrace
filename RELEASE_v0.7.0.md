# 🌱 EcoTrace v0.7.0 — The VS Code Intelligence Update

**Release Date:** 09.04.2026
**Ecosystem Version:** v0.7.0  
**Extension Version:** v0.7.0 (Official Launch)  
**Focus:** Official VS Code Extension & Real-time IDE Monitoring

---

## 🌟 What's New

### 🖥️ Official VS Code Extension (EcoTrace: Python Carbon Monitor)
EcoTrace v0.7.0 marks our transition from a standalone library to a **fully integrated developer ecosystem**. We are officially launching the EcoTrace VS Code Extension on the Microsoft Marketplace.

- **Real-Time Status Bar Updates:** Monitor your code's carbon footprint (gCO2) function-by-function, directly in your VS Code status bar.
- **Session Cumulative Tracking:** Keep track of your total carbon impact throughout your entire coding session—know your footprint before you even close the terminal.
- **Visual Carbon Indicators:** The status bar turns into a warning state (amber) if a single function triggers high-carbon heuristics (>0.1g), allowing for immediate optimization.
- **One-Click Reports:** Instantly open your last generated `ecotrace_full_report.pdf` directly from the IDE with built-in commands.

### 📚 Hybrid Documentation Engine
We’ve revamped the internal documentation of our core extension source code to match the "Hybrid" standard of the main EcoTrace library.
- **JSDoc Integration:** Full technical documentation for all extension lifecycle hooks (`activate`, `deactivate`) and core data flows.
- **Technical Resilience:** Documented implementation logic for overcoming OS-level file contention and high-frequency lock issues during continuous sampling.

### 🛠️ Ecosystem Synchronization
- **Centralized Roadmap:** The project README has been updated to include a permanent "VS Code Extension" section with direct installation links.
- **Optimized Packaging:** Refined the extension internal name to `ecotrace-monitor` to ensure a unique, conflict-free presence in the Marketplace.
- **Git Alignment:** The repository now follows a streamlined Monorepo structure, holding both the core Python engine and the VS Code extension source in perfect harmony.

---

## 🚀 Getting Started with the Extension

You can now install EcoTrace directly from within VS Code:
1. Open **Extensions** (Ctrl+Shift+X).
2. Search for **"EcoTrace"**.
3. Install **EcoTrace: Python Carbon Monitor**.
4. Run your EcoTrace-instrumented Python code as usual and watch the status bar come to life!

---

## 📦 How to Upgrade Core Library
```bash
pip install --upgrade ecotrace
```

*Bringing carbon intelligence where it belongs: directly into your editor.*
