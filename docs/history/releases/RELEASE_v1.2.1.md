# Release Notes — v1.2.1

**Released:** 2026-06-03
**Type:** Patch Release — Bug Fixes & Security Updates

---

## Summary

v1.2.1 is a quality-of-life and security patch release addressing compatibility bugs, API vulnerabilities, and alignment issues identified in the v1.2.0 release.

---

## Changes & Fixes

### 1. Robust Windows RAM Detection
Replaced deprecated `wmic` with PowerShell `Get-CimInstance` for Windows RAM speed detection, resolving issues on Windows 11 24H2 where `wmic` has been removed. Added robust local exception handling for `dmidecode` on Linux to ensure fallback to `sudo -n` works seamlessly even if non-sudo execution raises environment errors.

### 2. Machine Learning Tracker Enhancements (`EcoTraceML`)
- **Constructor Parameters:** Added missing `project_name`, `epochs`, `batch_size`, and `dataset_size` parameters to both `EcoTraceML` context manager and `@ecotrace_ml` decorator as documented in v1.2.0.
- **CSV Headers Alignment:** Aligned the logging header and columns produced by `EcoTraceML` with the main `EcoTrace` core format, resolving parse errors during `ecotrace analyze` CLI and JSON export phases.

### 3. Security Hardening
- Switched the user region check API from HTTP (`http://ip-api.com`) to HTTPS (`https://ip-api.com`) to prevent MITM tampering.
- Made the `USER_AGENT` resolve dynamically based on the installed package version.
- Updated supported releases in `SECURITY.MD` to include `v1.2.x` and `v1.1.x`.

### 4. Code & Lifecycle Improvements
- Renamed the misleading `WATTS_PER_KILOWATT` variable to `MILLIWATTS_PER_WATT` in GPU NVML power scaling.
- Implemented class-level `atexit` registration with `WeakSet` in `EcoTrace` to avoid duplicate session summaries when handling multiple concurrent tracking instances.
