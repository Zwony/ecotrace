# Release Notes — v0.6.1

**Release Date:** 2026-04-04
**Type:** Patch Release

---

## Overview

v0.6.1 establishes community governance standards for the EcoTrace project and includes several reliability and diagnostics improvements to the engine.

---

## Added

**Community and Security Standards**

- Adopted the Contributor Covenant v2.1 Code of Conduct.
- Published a Security Policy with a dedicated private reporting channel (`ecotraceteam@gmail.com`).
- Updated CONTRIBUTING guidelines to integrate the new governance standards.

**Unified Project Identity**

- Official team email `ecotraceteam@gmail.com` replaces personal contact points across all documentation and package manifests.
- `pyproject.toml` and `README.md` updated to reflect the EcoTrace Team identity.

---

## Fixed

- **API Identity (User-Agent):** All network requests to Electricity Maps and PyPI now identify themselves as `EcoTrace/0.6.1`, improving compatibility with API security layers.
- **Enhanced Diagnostics:** The PDF reporting engine now logs specific failure details instead of a generic error, helping debug permission and filesystem issues.
- **Code Cleanup:** Removed unused imports and refined internal logic.

---

## Compatibility

This is a fully backward-compatible patch release. No API changes were introduced.

---

## How to Upgrade

```bash
pip install --upgrade ecotrace
```
