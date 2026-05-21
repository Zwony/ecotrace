# Release Notes — v0.7.1

**Release Date:** 2026-04-18 **Type:** Patch Release

---

## Overview

v0.7.1 introduces a dedicated VS Code Sidebar Dashboard, editor hotspot annotations, and source location capture in the core instrumentation engine.

---

## Added

**VS Code Sidebar Dashboard** A dedicated panel in the VS Code Activity Bar displays aggregate carbon footprint and identifies the top carbon-consuming functions without leaving the editor.

**Editor Hotspot Annotations** EcoTrace automatically marks tracked functions in the editor gutter. Hover tooltips display carbon consumption data directly above the function definition.

**Source Location Intelligence** The core instrumentation engine now captures the source file path and line number for all tracked functions. This metadata is used by the VS Code visualization layer and enables precise cross-referencing between emission logs and source code.

---

## Updated

- Optimized CSV logging to prevent file contention during high-frequency monitoring sessions.
- Verified full backward compatibility with the v0.7.0 instrumentation pipeline.
- VS Code Extension bumped to v0.8.0.

---

## How to Upgrade

```
pip install --upgrade ecotrace
```

The VS Code Extension updates automatically via the Marketplace, or can be updated manually through the Extensions view.
