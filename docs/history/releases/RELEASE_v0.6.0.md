# Release Notes — v0.6.0

**Release Date:** 2026-04-01
**Type:** Minor Release

---

## Overview

v0.6.0 replaces static carbon intensity averages with real-time grid data via Electricity Maps, introduces IP-based region auto-detection, expands global coverage to 50+ regions, and adds an interactive auto-update system.

---

## Added

**Live Grid API — Electricity Maps Integration**

Real-time carbon intensity data replaces static country averages when a `grid_api_key` is provided.

- 38 global zones mapped to Electricity Maps region identifiers.
- 1-hour in-memory cache to limit unnecessary network requests.
- Automatic silent fallback to static IEA averages when no key is provided or a network error occurs.

**Automatic Region Detection**

When no `region_code` is provided at initialization, EcoTrace queries a lightweight public IP-API to detect the user's country code and match it against the carbon intensity database.

- Default region changed from `"TR"` to `"GLOBAL"` for a more appropriate international default.

**Expanded Global Coverage**

Coverage extended to 50+ strategic regions, including Ireland (IE), Israel (IL), Taiwan (TW), UAE (AE), and Colombia (CO).

**Auto-Update System**

- Non-blocking startup check for new PyPI releases.
- Interactive upgrade prompt in terminal environments.
- Automatically skipped in non-interactive CI/CD environments or when `check_updates=False` is set.

**Engine Refinements**

- Initialization replaced with a structured hardware profiling banner.
- Added `EcoTrace(quiet=True)` to suppress all standard output — intended for production logs and CLI tool integration.
- New test suite (`test_v6_features.py`) with mock integration for network failure and API stress testing.

---

## Compatibility

Existing code requires no modification. The only behavioral change is that users who previously relied on the implicit `"TR"` default will now receive the global average or auto-detected local region.

---

## How to Upgrade

```bash
pip install --upgrade ecotrace
```
