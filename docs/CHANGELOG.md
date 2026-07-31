# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2026-07-31

### Added
- **`CloudExporter` & Native `EcoTrace(api_key="eco_usr_...")` Integration**: Direct, zero-config telemetry streaming from Python applications to the EcoTrace Hosted Web Dashboard using private ingestion keys.
- **CLI Authentication & Credential Management**: Added `ecotrace login --key eco_usr_...`, `ecotrace logout`, and `ecotrace status` terminal subcommands to securely manage credentials in `~/.ecotrace/config.json`.
- **Automatic CLI Telemetry Streaming**: `ecotrace run <script.py>` now automatically attaches saved credentials and streams execution runs to the user's web dashboard.
- **Web Backend WebSocket Live Channel**: Implemented `/api/ws/live` WebSocket channel on FastAPI backend for real-time metric streaming to active web dashboard sessions.
- **6,980+ Unique CPU TDP Database Expansion**: Expanded `cpu_data.csv` to 6,983 unique CPU models with 100% valid TDP ratings, increasing laptop/mobile CPU coverage by +760% (1,520+ mobile CPUs including Intel 10th-14th Gen H/U/P/HX, Core Ultra, AMD Ryzen 3000-8000 mobile, and Apple Silicon M1-M4).
- **Expanded Python Version Compatibility**: Extended Python compatibility from `Python 3.9-3.12` to **`Python 3.8 → 3.14+`** across `pyproject.toml`, documentation, marketplace manifests, and landing page metrics.

## [1.4.3] - 2026-07-28

### Fixed
- **CPU TDP Database Path Resolution**: Fixed invalid file path in `core.py` targeting non-existent `boaviztapi/data/crowdsourcing/` path. Redirected to `cpu_data.csv` (7,390+ CPU dataset, 100% verified TDP coverage) to ensure TDP database is actually loaded into memory instead of silently falling back to generic 65W for all x86 chips.
- **Enhanced CPU Model Matching Algorithm**: Upgraded string resolution in `cpu.py` to support bidirectional containment checks, noise word stripping (`cpu`, `processor`), and length-descending model sorting so specific chips (e.g. `i7-10700K`, `EPYC 7B12`, `i7-13700H`) match their exact TDP boundaries.

### Changed
- **Repository Cleanup**: Removed 164 unused BoaviztAPI documentation, test, and build artifacts from git index, updating `.gitignore` to prevent tracking non-runtime assets.

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
- **Pausable Tracking API (`pause()` / `resume()`):** Temporarily disable carbon tracking during setup, teardown, or data loading phases. The paused duration is excluded from the session summary automatically.
- **`ecotrace diff` command:** Side-by-side carbon footprint comparison of any two runs. Shows per-function call count, duration, and gCO2 deltas. Supports `--latest` shortcut for CI/CD pipelines.
- **`WebhookExporter`:** Push carbon metrics to any webhook in real-time (Slack, MS Teams, Discord, custom APIs). Integrates with the existing `add_exporter()` API.
- **Filtered CSV Export:** Extended `ecotrace export` with `--csv` format and `--run`/`--func` filter options for targeted data extraction.
- **`ecotrace clean` command:** Rotate the CSV audit log by run count (`--keep-runs`) or date (`--before`). Creates an automatic `.bak` backup before trimming.
- **`ecotrace reset` command:** Delete the CSV log file entirely with a confirmation prompt (`--yes` flag for non-interactive use).

### Fixed
- **Duplicate Carbon Calculations:** Removed duplicate and fragile carbon formulas in Keras and PyTorch callbacks — now delegates cleanly to `EcoTraceML.log_epoch()`.
- **Empty GPU monitoring crash:** Guarded `EcoTraceML` shutdown sequence against empty GPU monitor histories to prevent `IndexError` on CPU-only machines.
- **Async Metadata propagation:** Propagated source file paths and line numbers correctly in `measure_async()`, restoring hotspot tracking for async functions.
- **CPU Cache Optimization:** Eliminated duplicate `cpuinfo.get_cpu_info()` calls in `get_cpu_info` by reusing the cached `fetch_raw_cpu_info()` result.

## [1.3.0] - 2026-06-13

### Added
- **Multi-Run History (`ecotrace history` / `ecotrace trends`):** Every `EcoTrace` session now gets a unique `RunID` and optional `run_label`. The `ecotrace history` CLI command groups the CSV audit log by run and prints a per-run carbon summary. `ecotrace trends` renders an ASCII bar chart of emissions across the last N runs, making it easy to see whether code is getting greener over time.
- **`--label` flag for `ecotrace run`:** Tag any CLI session with a human-readable label (e.g. `ecotrace run my_script.py --label nightly-build`) that is stored in every CSV row of that run.
- **`get_summary()` API:** New `EcoTrace.get_summary() -> dict` method returns all session metrics — run ID, duration, total carbon, budget status, hardware info, and carbon equivalence — as a structured dictionary. Enables integration with notebooks, dashboards, and custom reporting pipelines without parsing stdout or CSV.
- **Apple Silicon `powermetrics` Support:** `HardwareMonitor` now detects Apple Silicon (M-series) Macs and reads exact CPU package energy via `sudo -n powermetrics`. Falls back to Boavizta estimation silently if `powermetrics` is unavailable — consistent with the existing RAPL fallback pattern.
- **ML Framework Callbacks (`ecotrace.callbacks`):** New `EcoTracePyTorchCallback` and `EcoTraceKerasCallback` classes provide per-epoch carbon breakdowns for training loops. Both use **lazy imports** — neither PyTorch nor TensorFlow is required at install time. Install optionally with `pip install ecotrace[ml]` or `pip install ecotrace[keras]`.
- **Live Dashboard (`ecotrace dashboard`):** New `ecotrace dashboard [--port 8585]` CLI command starts a lightweight localhost HTTP server (zero external dependencies — stdlib only) serving a real-time browser dashboard. Features: carbon timeline chart, per-function emissions bar chart, run history table, run filter dropdown, and carbon equivalence display. Auto-refreshes every 5 seconds.
- **`EcoTraceML.snapshot_energy()`:** New method for reading intermediate GPU energy values during training without stopping the monitoring thread.
- **`EcoTraceML.log_epoch()`:** Logs per-epoch energy/carbon to the CSV audit log, used internally by the ML callbacks.

### Changed
- Session summary now displays the `RunID` (and label if set).
- `_print_session_summary()` refactored to delegate to `get_summary()`, eliminating duplicated logic.
- CSV audit log headers updated: `RunID` and `RunLabel` columns appended at the end for full backward compatibility with existing log files.
- `export_json()` now includes `run_id` and `run_label` in the `meta` block.

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
