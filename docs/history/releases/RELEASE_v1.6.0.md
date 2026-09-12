# Release Notes — v1.6.0

**Release Date:** September 13, 2026  
**Tag:** `v1.6.0`  
**PyPI Package Version:** `1.6.0`  

---

## Overview

EcoTrace **v1.6.0** introduces multi-GPU automatic discovery and continuous tracking, DDR3 RAM hardware detection, and a persistent offline disk retry queue for the Cloud Exporter. This release also delivers a comprehensive overhaul of type annotations, removing static diagnostic errors across IDE language servers and hardening exception handling for production stability.

---

## Key Improvements in v1.6.0

### 1. Multi-GPU Automatic Tracking and Power Aggregation (`ecotrace.gpu` & `ecotrace.core`)
- **Automated GPU Enumeration:** All available NVIDIA GPUs are automatically detected via NVML device enumeration (`get_all_gpu_info`).
- **Aggregated Power Metrics:** Continuous 50 ms power measurement reads instantaneous draw across all active NVIDIA GPUs (`get_all_gpu_power_w`) or aggregates individual GPU TDP limits for non-NVML estimation.
- **Deprecation of `gpu_index`:** Selecting single GPUs via `gpu_index` is deprecated in favor of unified multi-device monitoring. Supplying `gpu_index > 0` emits a backward-compatible `DeprecationWarning`.
- **Telemetry Hardware Reporting:** Startup logs, session summaries, and exported JSON/CSV artifacts now include comprehensive GPU array information (GPU count, device models, and total combined TDP).

### 2. DDR3 RAM Speed Detection (`ecotrace.ram`)
- **Legacy Server Architecture Support:** Evaluates memory clock frequencies between 800 MHz and 2133 MHz via Linux `dmidecode` and Windows Management Instrumentation (WMI) to detect DDR3 memory.
- **Calibrated Power Factor:** Correctly applies the DDR3 watt consumption factor (0.500 W/GB vs. DDR4 0.375 W/GB and DDR5 0.280 W/GB), improving carbon accounting accuracy on older enterprise infrastructure.

### 3. Cloud Exporter Offline Disk Retry Queue (`ecotrace.exporters.cloud`)
- **Resilient Telemetry Persistence:** Network dropouts, connection timeouts, and backend 5xx errors no longer cause telemetry data loss. Payloads are persisted to an isolated local disk queue (`~/.ecotrace/retry_queue`).
- **Automatic Queue Flushing:** Once network connectivity is restored, queued payloads are automatically flushed and ingested in chronological order.
- **Queue Bounds Enforcement:** Imposes a strict 50-entry FIFO ceiling on the retry directory to avoid unbound local disk utilization.

### 4. Static Type Safety and Diagnostics Overhaul
- **Strict Type Annotations:** Completely eliminated `# type: ignore` workarounds in favor of explicit `TYPE_CHECKING` imports, `Optional[...]` annotations, and runtime type narrowing.
- **Clean IDE Diagnostics:** Resolved 7 static type inference warnings across `core.py`, `gpu.py`, and exporters under Pyrefly, Pyright, and Pylance.
- **Clean Exception Flow:** Refactored function wrappers to prevent suppressed exceptions and ensure reliable metric calculation.

---

## Verification & Test Suite

- **100% Test Pass Rate:** All 140 unit and integration tests passed cleanly across core tracking, multi-GPU emulation, cloud retry queues, hardware detection, and middleware.
- **Full Compatibility:** Verified against Python 3.8 through Python 3.14+.
