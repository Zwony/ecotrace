# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

# [0.9.0] - 2026-04-30
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
