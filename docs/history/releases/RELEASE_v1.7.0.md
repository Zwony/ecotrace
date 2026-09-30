# Release Notes — v1.7.0

**Release Date:** 2026-09-30  
**Tag:** `v1.7.0`  
**PyPI Package Version:** `1.7.0`  

EcoTrace **v1.7.0** introduces native **LangChain integration** (`EcoTraceLangChainCallback`) for LLM and RAG pipelines, major **Global Grid Database expansion** covering 209 countries with verified Ember Climate data, responsive **Terminal ASCII Table Analytics** (`ecotrace analyze --table`), and clean architectural refactoring for CPU Thermal Design Power (TDP) resolution.

---

## Key Improvements in v1.7.0

### 1. Native LangChain & RAG Carbon Tracking
- Added `EcoTraceLangChainCallback` in `ecotrace.callbacks.langchain` with clean inheritance from LangChain's `BaseCallbackHandler`.
- Independent `run_id` isolation ensures thread-safe tracking during concurrent invocations, chains, and async agent runs.
- Tracks per-call execution duration, model identifier, instantaneous power, operational carbon ($gCO_2$), and provider token usage.
- Includes `examples/langchain_tracking.py` running offline with zero hard dependencies.
- Contributed by **@Gthejesraj** in [#198](https://github.com/Zwony/ecotrace/pull/198).

### 2. Global Carbon Grid Expansion (200+ Countries & Territories)
- Upgraded `CARBON_INTENSITY_MAP` in `ecotrace/constants.json` from 47 regions to **209 verified countries and territories** (+ `GLOBAL` and `DEFAULT`).
- Sourced directly from Ember Climate's latest 2025/2026 global electricity generation metrics.
- Provides instantaneous local carbon intensity resolution in offline environments with zero API tokens or network calls.

### 3. Responsive ASCII Terminal Table Reporting
- Added `--table` flag to `ecotrace analyze` (`ecotrace analyze --table`).
- Bordered ASCII table dynamically adapts to terminal width across 3 tiers (standard 4-column, narrow 3-column, and compact 2-column) without wrapping.
- Computes comprehensive column totals across all recorded functions while capping display cleanly.
- Built strictly using Python standard library with zero external dependencies.
- Contributed by **@hajar-benhadj** in [#197](https://github.com/Zwony/ecotrace/pull/197) / [#199](https://github.com/Zwony/ecotrace/pull/199).

### 4. Hardware Resolution Refactoring
- Purged legacy hardcoded `TDP_MAP` dictionary from `constants.json`.
- Unified processor matching for all architectures (Intel Core, AMD Ryzen, Apple Silicon M-series) directly against the verified 6,980+ CPU specification dataset (`cpu_data.csv`).

### 5. OpenSSF Security Hardening
- Enforced branch protection rules and CodeQL status checks on `main`.
- Established repository `.github/CODEOWNERS` and configured `codecov.yml` exclusion filters.
- Matrix unit tests pinned across Python 3.8 through Python 3.14-dev (212 tests passing).
