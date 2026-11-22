# Release Notes — v1.9.0

**Release Name:** EcoTrace Observability & Reporting Release

**Tag:** `v1.9.0`

**PyPI Package Version:** `1.9.0`

**Date:** 2026-11-22

EcoTrace **v1.9.0** adds Prometheus Pushgateway support and shareable Markdown and HTML session reports. This community-driven release also includes a Polars profiling example and a CI/CD and Docker troubleshooting guide. EcoTrace now requires Python 3.11 or later.

---

## Community Contributions

Thank you to everyone who helped shape this release.

- **@foojanbabaeeian** added the Prometheus Pushgateway exporter, with separate metric groups for each tracked function and run. [#250](https://github.com/Zwony/ecotrace/pull/250)
- **@Taiye03** added Markdown and HTML session reports and exposed cumulative energy use through `EcoTrace.get_summary()`. [#252](https://github.com/Zwony/ecotrace/pull/252)
- **@R4M0S17** contributed a Polars profiling example, a guide for eager and lazy workloads, and integration tests. [#251](https://github.com/Zwony/ecotrace/pull/251)
- **@sehr-abrar** wrote the FAQ and troubleshooting guide for CI/CD and Docker environments. [#248](https://github.com/Zwony/ecotrace/pull/248)
- **@Zwony** updated contributor documentation and added guidance on sponsorship and institutional partnerships. [#247](https://github.com/Zwony/ecotrace/pull/247), [#256](https://github.com/Zwony/ecotrace/pull/256)

---

## Key Features & Highlights

### 1. Prometheus Pushgateway Exporter

`PrometheusExporter` sends carbon emissions and execution duration after each tracked measurement. Each function and run has its own Pushgateway group, which retains its latest values until replaced or deleted.

```python
from ecotrace import EcoTrace
from ecotrace.exporters import PrometheusExporter

eco = EcoTrace()
PrometheusExporter(eco, url="http://localhost:9091")

with eco.track_block("workload"):
    sum(i * i for i in range(1_000_000))
```

### 2. Markdown & HTML Session Reports

Turn an EcoTrace session summary into a Markdown table for pull requests and CI summaries, or an HTML fragment for notebooks and dashboards. Both formats show the run label, total energy in kWh, duration, and estimated carbon emissions.

```python
from ecotrace.exporters import to_html, to_markdown

summary = eco.get_summary()
markdown_report = to_markdown(summary)
html_report = to_html(summary)
```

### 3. Polars Profiling & Troubleshooting Guides

- `examples/polars_workload.py` shows how to profile eager operations and lazy pipelines, including where to call `.collect()` so execution happens inside the tracked block.
- The new FAQ covers hardware sensor fallbacks, CI/CD environments, and Docker deployments.

---

## Security & Quality Gates

- **Python 3.11 minimum.** Python 3.8, 3.9, and 3.10 have reached upstream end of life. Upgrade Python before installing EcoTrace 1.9.0 on an environment using any of those versions. [Python version lifecycle](https://devguide.python.org/versions/)
- **Runtime dependencies.** The Prometheus exporter uses the existing `requests` dependency, and the Markdown and HTML renderers use the Python standard library.
- **Test coverage.** Added tests for Pushgateway request formatting and grouping, report rendering and escaping, and Polars profiling. The CI matrix targets Python 3.11 through 3.14 on Ubuntu 24.04.
