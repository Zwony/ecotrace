# Changelog

All notable changes to the EcoTrace project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
