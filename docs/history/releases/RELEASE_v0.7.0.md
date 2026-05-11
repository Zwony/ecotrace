# Release Notes — v0.7.0

**Release Date:** 2026-04-09
**Type:** Minor Release

---

## Overview

v0.7.0 marks the official launch of the EcoTrace VS Code Extension on the Microsoft Marketplace, transitioning EcoTrace from a standalone Python library to an integrated developer ecosystem with real-time IDE monitoring.

---

## Added

**Official VS Code Extension — EcoTrace: Python Carbon Monitor**

- Real-time status bar updates showing carbon footprint (gCO2) per function, directly inside VS Code.
- Session cumulative tracking: total carbon impact is tracked throughout the entire coding session.
- Visual carbon indicators: the status bar enters a warning state when a single function exceeds 0.1g CO2.
- One-click PDF report access: the last generated `ecotrace_full_report.pdf` can be opened directly from the IDE.

**Hybrid Documentation Engine**

Full technical documentation for all extension lifecycle hooks (`activate`, `deactivate`) and internal data flows, with implementation notes for OS-level file contention and high-frequency lock handling.

**Ecosystem Synchronization**

- Repository now follows a monorepo structure holding both the Python engine and the VS Code extension source.
- Extension internal name set to `ecotrace-monitor` for a unique, conflict-free Marketplace presence.
- README updated with a permanent VS Code Extension section and direct installation links.

---

## Getting Started with the Extension

1. Open Extensions in VS Code (Ctrl+Shift+X).
2. Search for "EcoTrace".
3. Install **EcoTrace: Python Carbon Monitor**.
4. Run any EcoTrace-instrumented Python script and observe the status bar.

---

## How to Upgrade

```bash
pip install --upgrade ecotrace
```
