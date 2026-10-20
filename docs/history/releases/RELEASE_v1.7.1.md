# Release Notes — v1.7.1

**Release Date:** 2026-10-20  
**Tag:** `v1.7.1`  
**PyPI Package Version:** `1.7.1`  

EcoTrace **v1.7.1** is a stability and performance patch addressing terminal scaling edge cases, redundant dataset parsing overhead, and defensive telemetry safeguards across production runtime environments.

---

## Key Improvements & Bug Fixes in v1.7.1

### 1. Terminal ASCII Table Bounds Guard (`ecotrace analyze --table`)
- Resolved an `IndexError: tuple index out of range` crash occurring when rendering bordered analysis tables in terminals narrower than 28 columns (common in IDE split-panes, mobile SSH sessions, and compact terminal multiplexers).
- Dynamically bounds the `Time (s)` duration column to ensure row cells strictly align with rendered headers across all terminal width tiers.
- Added automated matrix unit tests verifying terminal rendering across 20, 25, 27, 35, 45, 60, and 100 column widths.

### 2. High-Performance In-Memory CPU Specification Caching
- Equipped `load_tdp_database` with `functools.lru_cache(maxsize=1)` to avoid repeatedly parsing the 930 KB `cpu_data.csv` (6,980+ processors) on successive `EcoTrace()` or `EmissionsTracker()` instantiations.
- Yields immediate CPU overhead reduction and microsecond instantiation latencies.

### 3. Defensive Isolation in LangChain Tracking Callback
- Wrapped invocation initialization (`_begin`) and finalization (`_finish`) in `EcoTraceLangChainCallback` within defensive exception handling.
- Ensures that unexpected runtime telemetry or permission anomalies fail silently via debug logging without ever interrupting host LLM inference, RAG pipelines, or autonomous agent runs.

### 4. Container & Restricted Environment Safeguards
- Hardened `get_cpu_info` against environments where `psutil.cpu_count(logical=True)` returns `None` (e.g. constrained Docker containers, chroot jails, or virtualized environments), guaranteeing a safe fallback to 1 core.

### 5. Hardware Configuration Map Completeness
- Added explicit `"nvidia": 150.0` default entry to `GPU_TDP_DEFAULTS` in `constants.json`, aligning the static configuration schema with runtime GPU fallback branches.
