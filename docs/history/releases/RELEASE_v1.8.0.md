# Release Notes — v1.8.0

**Release Name:** EcoTrace Community & Hardware Expansion Release  
**Tag:** `v1.8.0`  
**PyPI Package Version:** `1.8.0`  
**Date:** 2026-11-01  

EcoTrace **v1.8.0** is a major minor-release powered by open-source community contributors, introducing rich card exporter payloads (Slack Block Kit and Discord Embeds), session CSV file exports for CLI executions, reference FastAPI middleware integration, and broadened next-generation hardware coverage spanning Apple Silicon M4, Intel Core Ultra, and AMD Ryzen 9000 processors.

---

## Community Contributions

A huge thank you to our community contributors who shaped this release:

- **@Aqureshi106** in [#229](https://github.com/Zwony/ecotrace/pull/229) — Added rich Discord embed and Slack Block Kit payload formats to `WebhookExporter` with configurable budget-aware embed color coding.
- **@awais-ur-rehman** in [#233](https://github.com/Zwony/ecotrace/pull/233) — Added automatic one-row session summary CSV export to `ecotrace run --output / -o <file.csv>`.
- **@Vritika22Mandapaka** in [#228](https://github.com/Zwony/ecotrace/pull/228) — Added a comprehensive reference integration example in `examples/fastapi_tracking.py` demonstrating `EcoTraceMiddleware` and per-request carbon headers.

---

## Key Features & Highlights

### 1. Rich Discord & Slack Webhook Exporters
`WebhookExporter` now supports specialized message formatting via the `format` parameter:
- `WebhookExporter(eco, url, format="discord")`: Posts structured Discord embeds displaying function name, duration, and carbon emissions. Automatically colors embeds green (`0x2ECC71`) when emissions remain under `carbon_limit`, or red (`0xE74C3C`) when exceeding budget.
- `WebhookExporter(eco, url, format="slack")`: Posts Slack Block Kit sections with formatted metric fields and plain text fallback.
- `format="json"` remains the default, guaranteeing 100% backward compatibility.

### 2. CLI Run Session CSV Export
Developers can now persist execution summaries directly into CSV tables without stdout redirection:
```bash
ecotrace run -o session.csv my_script.py
ecotrace run --output report.json my_script.py
```
Automatically infers format by extension (`.csv` vs `.json`) with clean nested object serialization.

### 3. Next-Generation Hardware Database Coverage
Added verified architecture and Thermal Design Power (TDP) profiles to `ecotrace/cpu_data.csv`:
- **Apple Silicon:** M4 Pro (35W) and M4 Max (78W).
- **Intel Core Ultra (Arrow Lake & Meteor Lake):** 285K (125W), 265K (125W), 245K (125W), 185H (45W), 155H (28W), and 125H (28W).
- **AMD Ryzen 9000 (Zen 5):** 9950X (170W), 9900X (120W), 9700X (65W), and 9600X (65W).

### 4. Official Ecosystem Guides
- Added end-to-end documentation for LangChain callback tracking and HuggingFace Transformers Trainer callbacks in `docs/integrations/`.
- Included PyTorch model inference profiling in `examples/pytorch_inference.py`.

---

## Security & Quality Gates
- **Zero New Dependencies:** Core package remains strictly zero-dependency (relying only on standard library and existing base libraries).
- **Continuous Integration:** 253/253 unit tests passing across Python 3.8 through 3.14-dev.
- **Supply Chain Security:** Maintained OpenSSF Scorecard dependency pinning, SonarCloud Clean Code rating, and automated CodeQL vulnerability scanning.
