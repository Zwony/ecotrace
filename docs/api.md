# API Reference

This page provides the complete technical documentation for all public modules in EcoTrace.

---

## Core Module

The `EcoTrace` class is the main entry point for all monitoring operations.

::: ecotrace.core
    options:
      show_root_heading: true
      show_source: true
      members_order: source

---

## CLI Module

Technical details of the Command Line Interface (`ecotrace run`, `ecotrace gate`, etc.).

::: ecotrace.cli
    options:
      show_root_heading: true
      show_source: false

---

## Report Module

Generates PDF and CSV carbon audit reports.

::: ecotrace.report
    options:
      show_root_heading: true
      show_source: false

---

## Hardware Module

Auto-detects CPU, GPU, and RAM specifications.

::: ecotrace.hardware
    options:
      show_root_heading: true
      show_source: false

---

## CPU Module

CPU TDP lookup and energy estimation logic.

::: ecotrace.cpu
    options:
      show_root_heading: true
      show_source: false

---

## GPU Module

GPU power monitoring (NVIDIA NVML, AMD/Intel WMI).

::: ecotrace.gpu
    options:
      show_root_heading: true
      show_source: false

---

## RAM Module

Process-scoped memory usage and energy calculation.

::: ecotrace.ram
    options:
      show_root_heading: true
      show_source: false

---

## Config Module

Region validation, carbon intensity resolution, and Live Grid API integration.

::: ecotrace.config
    options:
      show_root_heading: true
      show_source: false

---

## Exceptions Module

All domain-specific exceptions raised by EcoTrace.

::: ecotrace.exceptions
    options:
      show_root_heading: true
      show_source: false

---

## Middleware

### Flask (`ecotrace.middleware.flask`)

::: ecotrace.middleware.flask
    options:
      show_root_heading: true
      show_source: false

### FastAPI / Starlette (`ecotrace.middleware.fastapi`)

::: ecotrace.middleware.fastapi
    options:
      show_root_heading: true
      show_source: false

---

## Plugins

### pytest Plugin (`ecotrace.plugins.pytest_plugin`)

::: ecotrace.plugins.pytest_plugin
    options:
      show_root_heading: true
      show_source: false
