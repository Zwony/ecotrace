# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
