# Changelog

All notable changes to the EcoTrace project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2026-04-24

### Added
- **CLI Profiler (`ecotrace run`):** Run any Python script under full carbon monitoring without modifying source code. Uses `runpy.run_path` for same-process isolation.
- **CLI Analysis (`ecotrace analyze`):** Parse existing `ecotrace_log.csv` and display a ranked carbon summary table in the terminal.
- **CLI Export (`ecotrace export --json`):** Export hardware metadata, measurement history, and aggregate statistics to a structured JSON file.
- **CLI Benchmark (`ecotrace benchmark`):** Self-diagnostic tool that measures EcoTrace's own CPU overhead as a percentage of total execution time.
- **JSON Export API (`eco.export_json()`):** New method on the `EcoTrace` class for programmatic JSON export — serves as the data bridge for the VS Code extension.
- **`python -m ecotrace` Support:** Package-level `__main__.py` module for direct module invocation.

### Updated
- Bumped version to 0.8.0 across `pyproject.toml`, `__init__.py`, and `config.py`.
- Added `[project.scripts]` entry point for system-wide `ecotrace` command availability after `pip install`.

## [0.7.1] - 2026-04-18

### Added
- **VS Code Sidebar Dashboard:** Integrated control panel for real-time visualization of aggregate carbon usage and high-impact functions.
- **IDE Editor Hotspots:** Automatic gutter markers with carbon consumption tooltips directly within the code editor.
- **Source Location Capture:** Automated tracking of function source locations (file/line) to enable IDE cross-referencing.
- **Professional Linguistic Polish:** Refined all internal documentation and code comments for clarity and technical precision.

### Updated
- Optimized CSV logging performance to ensure stability during high-throughput monitoring.
- Scaled up the versioning for both the core library (0.7.1) and VS Code extension (0.8.0).

## [0.7.0] - 2026-04-09

### Added
- **VS Code Extension (Official Launch):** Integrated real-time carbon monitoring directly in the IDE status bar.
- **Electricity Maps API Integration:** Live grid intensity data fetching with 1-hour intelligent caching.
- **Auto-Update System:** Interactive version check at startup via PyPI.
- **Process Tree Intelligence:** Recursive CPU and RAM tracking for multiprocessing applications.
- **Idle Baseline Subtraction:** 100ms system noise filtration for higher measurement precision.
- **Comparison Engine:** Side-by-side analysis of two functions (`eco.compare`).

### Fixed
- Fixed `psutil.AccessDenied` issues during recursive process scanning.
- Improved error handling in PDF report generation with better font sanitization.

## [0.6.1] - 2026-04-04

### Added
- Support for NVIDIA, AMD, and Intel GPUs via `nvidia-ml-py` and `WMI`.
- Dedicated `@track_gpu` decorator.
- Google Gemini AI integration for "Green Coding" optimization insights.

## [0.6.0] - 2026-04-01

### Added
- Core instrumentation engine with 50ms daemon-thread sampling.
- Boaviztapi TDP database integration (1,800+ models).
- PDF Audit report generation with Matplotlib charts.
- Asyncio support for `@track`.

## [0.4.0] - 2026-03-20

### Added
- Initial release of the TDP-based carbon estimation logic.
- Basic CSV logging system.
- Static region-based carbon intensity mapping.

---
*For a detailed walkthrough of each release, see the `RELEASE_vX.Y.Z.md` files in the repository.*
