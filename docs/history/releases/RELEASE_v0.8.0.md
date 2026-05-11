# Release Notes — v0.8.0

**Release Date:** 2026-04-24
**Type:** Minor Release

---

## Overview

v0.8.0 introduces a unified command-line interface, JSON export support for VS Code extension integration, and direct module invocation via `python -m ecotrace`.

---

## Added

**Unified CLI Tool**
The `ecotrace` command-line interface is now available with the following subcommands:

| Subcommand | Description |
|---|---|
| `ecotrace run <script.py>` | Profile any script without modifying it |
| `ecotrace analyze <log.csv>` | Analyze a saved emission log |
| `ecotrace export <log.csv>` | Export log to JSON format |
| `ecotrace benchmark` | Run a standard CPU benchmark |

**JSON Export API**
`EcoTrace.export_json(path)` exports the full session emission log to a structured JSON file. Used by the VS Code extension to render real-time charts.

**`python -m ecotrace` Support**
The package now includes a `__main__.py` module enabling direct invocation:

```bash
python -m ecotrace run my_script.py
```

---

## Updated

- Version bumped to `0.8.0` across `pyproject.toml`, `__init__.py`, and `config.py`.
- Added `[project.scripts]` entry point so the `ecotrace` command is available system-wide after `pip install`.
