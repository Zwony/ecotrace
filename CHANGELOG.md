# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.2] - 2026-07-21

### Fixed
- **`ram_info` null safety**: Guarded `_compute_carbon` against `NoneType` `ram_info` returns to prevent crash loops.
- **`nvmlShutdown` global scope isolation**: Removed `pynvml.nvmlShutdown()` from instance `__del__` destructor to preserve global NVML state for concurrent instances.
- **Exception propagation in `measure()` & `measure_async()`**: Fixed exception handling in measurement teardown to prevent user function exceptions from being masked.
- **Dashboard Stored XSS**: Sanitized user inputs before DOM rendering in live web dashboard.
- **Dashboard CORS origin restriction**: Restricted `Access-Control-Allow-Origin` from wildcard `*` to localhost origin.
- **GitHub Action CLI integration**: Added `--region` flag support to `ecotrace gate` subcommand required by `action.yml`.
- **Updater fallback logic**: Replaced naive string inequality with integer tuple parsing for version comparison when `packaging` is absent.
- **Middleware lazy loading**: Implemented module `__getattr__` in `middleware/__init__.py` to avoid eager imports of web frameworks.
- **RAM power modeling**: Added watt factors for DDR3, LPDDR4, LPDDR5 and UNKNOWN RAM types.
- **PDF Report log path parameter**: Added configurable `log_file` parameter to `generate_pdf_report`.

## [1.4.1] - 2026-07-18

### Fixed
- **`track_block()` exception safety**: Restructured with `try/finally` so carbon is always logged even when user code raises exceptions inside the block, matching the behavior of `measure()` and `track_gpu()`.
- **GPU chart 3-tuple crash**: Normalized GPU samples to 2-tuples `(timestamp, utilization)` in `generate_pdf_report()` before passing to chart functions, preventing data format mismatches with the core engine's 3-tuple `(timestamp, utilization, power)` samples.
- **Django middleware naming**: Renamed `EcoTraceMiddleware` in `middleware/django.py` to `EcoTraceDjangoMiddleware` as documented in the v1.1.2 changelog. A backward-compatible alias is preserved for migration.
- **`plistlib` top-level import**: Moved the `plistlib` import from top-level in `hardware.py` into the macOS-only methods where it is actually used, following the project's established lazy-import pattern.
- **Dashboard stale version**: The live dashboard footer now dynamically resolves version from `ecotrace.__version__` instead of displaying a hardcoded `v1.3.0`.
- **CSV export default filename**: `ecotrace export --csv` now defaults output to `ecotrace_export.csv` instead of the format-mismatched `ecotrace_report.json`.
- **ML energy accumulation**: Added `total_energy_kwh` attribute to `EcoTrace.__init__` so `EcoTraceML` can correctly accumulate GPU energy across sessions.

## [1.4.0] - 2026-07-01

### Added
- **`ecotrace diff` command**: Side-by-side carbon footprint comparison of any two runs.
- **CSV Export options**: Extended `ecotrace export` with `--csv` format and `--run`/`--func` filters.
- **Pausing API**: `EcoTrace.pause()` and `EcoTrace.resume()` for temporarily disabling carbon tracking during setup/teardown.
- **`WebhookExporter`**: Push carbon metrics to webhooks in real-time (Slack, Teams, Discord, custom API).
- **`ecotrace clean` command**: Rotate/cleanup log CSV by run count or date, creating a backup automatically.
- **`ecotrace reset` command**: Reset/delete CSV log file completely with verification.

### Fixed
- **Duplicate Carbon Calculations**: Fixed duplicate and fragile carbon calculation in Keras and PyTorch callbacks.
- **Empty GPU monitoring crash**: Guarded `EcoTraceML` shutdown sequence against empty GPU monitor histories.
- **Async Metadata propagation**: Propagated source file paths and line numbers correctly in `measure_async()`.
- **CPU Cache Optimization**: Reused cached CPU information query in `get_cpu_info` instead of repeating py-cpuinfo parsing.

## [1.3.0] - 2026-06-13

### Added
- **Multi-Run Observability**: Unique Run ID and optional Run Label assigned to every session, written to CSV.
- **Run commands**: CLI subcommands `ecotrace history` and `ecotrace trends` for multi-run history inspection.
- **`get_summary()` API**: Programmatic session statistics for notebooks and test assertions.
- **Apple Silicon Support**: Direct hardware energy counter monitoring via `powermetrics`.
- **ML Framework Callbacks**: deferred callbacks `EcoTraceKerasCallback` and `EcoTracePyTorchCallback`.
- **Live Browser Dashboard**: Real-time HTTP dashboard served via `ecotrace dashboard` on port 8585.

## [1.2.1] - 2026-06-03

### Fixed
- **Windows RAM detection**: Replaced deprecated `wmic` with PowerShell `Get-CimInstance` for Windows RAM speed detection, preventing compatibility issues on Windows 11 24H2.
- **ML CSV alignment**: Aligned ML tracking CSV headers with the core engine's format to prevent parse mismatches.
- **ML constructor parameters**: Added missing `project_name`, `epochs`, `batch_size`, and `dataset_size` parameters to the `EcoTraceML` constructor and decorator.
- **API security**: Switched `ip-api.com` endpoint to HTTPS to protect against MITM attacks.
- **Dynamic User Agent**: Resolved dynamic package version in `USER_AGENT` to prevent stale version reports.
- **GPU naming**: Renamed misleading `WATTS_PER_KILOWATT` to `MILLIWATTS_PER_WATT` for Milliseconds to Watts NVML conversions.
- **Class-level atexit**: Implemented class-level exit handler using a `WeakSet` to prevent duplicate per-instance exit summaries.
- **Security Policy**: Updated supported versions in `SECURITY.MD` to include v1.2.x and v1.1.x.

## [1.2.0] - 2026-05-31
### Added
- **`EcoTraceML` tracking engine:** A context manager (`EcoTraceML`) and decorator (`@ecotrace_ml`) designed to track carbon footprint and energy consumption of machine learning model training.
- **Continuous hardware sampling:** Implemented multi-threaded background sampling for high-frequency hardware metrics polling.
- **ML test suite & example:** Added `tests/test_ml.py` and `example_ml.py` to demonstrate and verify ML tracking functionality.

### Fixed
- **NVIDIA NVML Windows compatibility:** Dynamic search and injection of Windows PATH for NVML DLLs, resolving import issues on Windows.
- **NVIDIA driver decode:** Safe fallback UTF-8 decoding for newer NVIDIA driver queries returning binary GPU names.
- **FPDF keyword issue:** Removed `txt` keyword argument from PDF cell generation to resolve strict Pylance/Type warnings.
- **Lazy imports:** Moved `google-generativeai` import inside `get_gemini_insights` to avoid startup `ModuleNotFoundError` when the `[ai]` extra is not installed.

## [1.1.2] - 2026-05-21
### Fixed
- **Session atexit:** Class-level `atexit` handler with `WeakSet` instances replaces per-instance registration.
- **measure / measure_async:** User exceptions propagate after measurement teardown; measurement errors no longer mask failures.
- **PDF / CSV:** `generate_pdf_report` accepts `log_path`; report CSV parsing uses `DictReader` column names.
- **Gemini import:** Lazy-load `google.generativeai` inside `get_gemini_insights` only.
- **Windows RAM:** PowerShell `Get-CimInstance` replaces deprecated `wmic`.
- **Linux RAM:** `dmidecode` without sudo first, then `sudo -n` when output is empty.
- **CPU info:** Reuses cached `fetch_raw_cpu_info()` instead of duplicate `cpuinfo` calls.
- **USER_AGENT:** Resolved from installed package version with fallbacks.
- **Update checker:** `_is_newer_version` returns `False` on parse failure.

### Changed
- **Breaking:** Django middleware renamed to `EcoTraceDjangoMiddleware` (`ecotrace.middleware.django`). FastAPI `EcoTraceMiddleware` unchanged.
- Logger default level restored to `WARNING`.

### Updated
- Version bumped to 1.1.2 across package metadata.

## [1.1.0] - 2026-05-19
### Added
- **OpenTelemetry Exporter:** Added `OTelExporter` for non-blocking export of carbon metrics to OpenTelemetry-compatible platforms such as Grafana, Datadog, New Relic, and Prometheus.
- **Django Middleware:** Added WSGI/ASGI request tracking with `X-Eco-Carbon-Emitted` and `X-Eco-Duration` response headers.
- **Celery Plugin:** Added task-level carbon tracking through Celery worker signals, including retry and revoke cleanup handling.
- **Exporter API:** Added `EcoTrace.add_exporter(exporter)` for registering custom exporter objects.

### Fixed
- **GPU TDP Resolution:** Runtime power limits are now used instead of factory default limits, improving estimates on power-capped GPUs.

### Updated
- Exporter dispatch now runs through a dedicated thread pool and flushes pending export tasks during process shutdown.
- Version bumped to 1.1.0 across package metadata.

## [1.0.1] - 2026-05-05
### Added
- **Carbon Budget Enforcement:** `carbon_limit` parameter now actively enforces budget with two-tier alerts (80% warning + 100% exceeded) and optional `on_budget_exceeded` callback.
- **Differential Tracking:** Idle baseline measurement is now subtracted from all CPU utilization readings, reporting only the energy cost of YOUR code — not OS background noise.
- **Session Summary:** Automatic `atexit` hook prints a formatted session summary (duration, functions tracked, total carbon, budget status) when the process exits.
- **Carbon Equivalences:** New `equivalence(gco2)` method converts abstract gCO2 values into human-readable comparisons (Google searches, LED bulb minutes, smartphone charges, Netflix streaming, car km).
- **CI/CD Carbon Gate:** New `ecotrace gate --budget 10.0` CLI command returns exit code 1 if accumulated emissions exceed the carbon budget. Designed for GitHub Actions / GitLab CI integration.
- **`remaining_budget` Property:** Programmatic access to remaining carbon budget for external consumers (IDE, dashboards).

### Fixed
- **Exception Swallowing:** `measure()` and `measure_async()` now properly re-raise user exceptions instead of silently returning `None`.
- **GPU `track_block` Crash:** Fixed tuple unpacking error when computing GPU carbon in `track_block()`.
- **GPU Chart Crash:** Fixed 3-tuple unpacking in `report.py` GPU chart generation.
- **Packaging:** Added `ecotrace.middleware` and `ecotrace.plugins` to distribution packages.
- **Optional Dependencies:** Moved `nvidia-ml-py`, `google-generativeai`, and `wmi` to optional extras (`pip install ecotrace[gpu]`, `[ai]`, `[all]`).

### Updated
- Logger default level changed from WARNING to INFO (initialization banner now visible).
- Version bumped to 1.0.1 across `pyproject.toml`, `__init__.py`, and `config.py`.

## [0.9.0] - 2026-04-30
### Added
- **Exact Mode (RAPL)**: Support for direct hardware energy counter monitoring on Linux (0% deviation).
- **Advanced Power Modeling**: Implementation of non-linear Boavizta load curves for precise estimation on Windows/macOS.
- **Hybrid Energy Engine**: Automatic hardware detection that selects the most accurate measurement method available.

## [0.8.0] - 2026-04-24

### Added
- **Unified CLI Tool:** Introduced the `ecotrace` command-line interface with `run`, `analyze`, `export`, and `benchmark` subcommands.
- **JSON Export API:** Added `export_json(path)` to the `EcoTrace` core to support VS Code extension integration.
- **`python -m ecotrace` Support:** Package-level `__main__.py` module for direct module invocation.

### Updated
- Bumped version to 0.8.0 across `pyproject.toml`, `__init__.py`, and `config.py`.
- Added `[project.scripts]` entry point for system-wide `ecotrace` command availability after `pip install`.

## [0.7.1] - 2026-04-18

### Added
- **Hotspot Highlighting:** Added support for capturing source file paths and line numbers during instrumentation.

### Updated
- Optimized CSV logging performance to ensure stability during high-throughput monitoring.
- Scaled up the versioning for both the core library (0.7.1) and VS Code extension (0.8.0).

## [0.7.0] - 2026-04-09

### Added
- **GPU Carbon Monitoring:** Real-time utilization tracking for NVIDIA GPUs via NVML.
- **Grid Carbon Intensity Fallback:** Automatic selection of static carbon data when Live Grid API is unavailable.
- **Memory Consumption Tracking:** Process-scoped RSS monitoring integrated into total emission calculation.
