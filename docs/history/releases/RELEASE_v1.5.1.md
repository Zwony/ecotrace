# Release Notes — v1.5.1

**Release Date:** August 15, 2026  
**Tag:** `v1.5.1`  
**PyPI Package Version:** `1.5.1`  

---

##  Overview

EcoTrace **v1.5.1** is a stability and telemetry compatibility patch release following v1.5.0. It resolves a Windows COM thread initialization crash in exporter background threads, restores full parameter forwarding (`run_id`, `run_label`) to `CloudExporter` for web dashboard filtering, standardizes exporter method signatures, and prevents eager circular imports.

---

##  Key Improvements & Fixes in v1.5.1

### 1. Windows COM Thread Pool Initialization Guard (`core.py`)
- **Prevented Windows Fatal Exception (`0x800401f0`)**: Wrapped worker thread execution in `_dispatch_exporters` with `CoInitialize` / `CoUninitialize` guards on Windows, preventing background COM crashes during exporter execution and garbage collection.

### 2. Full Parameter Forwarding for `CloudExporter` (`core.py` & `cloud.py`)
- **Dashboard Run Filtering Fixed**: Exporter dispatch now forwards `run_id` and `run_label` parameters to registered exporters, enabling the hosted dashboard session filtering engine.
- **Dynamic User-Agent Header**: Updated `CloudExporter` HTTP headers to resolve current package version dynamically.

### 3. Exporter Signature Consistency & Forward Compatibility
- Added `**kwargs` support to `CloudExporter`, `OTelExporter`, and `WebhookExporter` signatures to guarantee compatibility across past and future core engine versions.

### 4. Dynamic Exporter Module Lazy Loading (`exporters/__init__.py`)
- Implemented module-level `__getattr__` lazy loading in `ecotrace.exporters` to prevent eager imports and potential circular import dependencies.

### 5. Logger Level Alignment (`logger.py`)
- Restored `logging.WARNING` as default package log level across `ecotrace.logger` to align code behavior with documentation standards.

---

##  Verification & Test Suite
- **100% Test Pass Rate**: All 99 independent unit tests passed cleanly (`99 passed in 83s`).
- Verified zero Windows COM exceptions during thread pool metric dispatch.
