# Support and Reference

## Troubleshooting

**`psutil.AccessDenied` — Permission Denied** Run with elevated privileges or disable child process tracking if it is not required. EcoTrace will continue to operate in degraded mode.

**Missing GPU Drivers (NVIDIA / WMI)** EcoTrace detects the failure and falls back to CPU-only monitoring automatically. No configuration change is needed.

**`NoSuchProcess` Error** Occurs with extremely short-lived subprocess targets. The affected sample is discarded and monitoring continues.

**RAPL Not Available (Windows / macOS)** EcoTrace automatically selects the Boavizta advanced estimation model when RAPL hardware counters are unavailable.

---

## Data and Privacy

EcoTrace is local-first. No data leaves the machine unless one of the following optional features is explicitly enabled:

- **Live Grid API** — requires `grid_api_key` parameter
- **Gemini AI Insights** — requires `api_key` parameter
- **Update Check** — enabled by default, can be disabled with `check_updates=False`

---

## Global Coverage

EcoTrace supports 50+ regions using static IEA 2024 carbon intensity averages and live zone mappings via Electricity Maps.

| Code | Country | gCO2/kWh |  | Code | Country | gCO2/kWh |
| --- | --- | --- | --- | --- | --- | --- |
| SE | Sweden | 13 |  | US | United States | 367 |
| NO | Norway | 26 |  | DE | Germany | 385 |
| FR | France | 55 |  | TR | Turkey | 475 |
| CH | Switzerland | 95 |  | PL | Poland | 635 |
| CA | Canada | 130 |  | IN | India | 708 |
| NZ | New Zealand | 148 |  | AU | Australia | 790 |
| BR | Brazil | 175 |  | ZA | South Africa | 840 |
| FI | Finland | 191 |  | NG | Nigeria | 430 |
| AT | Austria | 210 |  | ID | Indonesia | 713 |
| GB | United Kingdom | 233 |  | CN | China | 555 |
| ES | Spain | 241 |  | KR | South Korea | 415 |
| NL | Netherlands | 283 |  | JP | Japan | 463 |
| PT | Portugal | 195 |  | TW | Taiwan | 510 |
| BE | Belgium | 165 |  | AE | UAE | 370 |
| IE | Ireland | 322 |  | SG | Singapore | 408 |
| DK | Denmark | 150 |  | TH | Thailand | 490 |
| CZ | Czech Republic | 410 |  | MY | Malaysia | 585 |
| HU | Hungary | 233 |  | PH | Philippines | 520 |
| RO | Romania | 290 |  | EG | Egypt | 460 |
| IT | Italy | 371 |  | AR | Argentina | 321 |
| GR | Greece | 334 |  | CO | Colombia | 196 |
| UA | Ukraine | 312 |  | CL | Chile | 300 |
| IL | Israel | 450 |  | KE | Kenya | 47 |
| MX | Mexico | 450 |  |  |  |  |

> For live carbon intensity data, provide a `grid_api_key` from [Electricity Maps](https://www.electricitymaps.com/) .

---

## Supported Hardware

### CPU

- Intel Core and Xeon (all generations in Boavizta database — 1,800+ models)
- AMD Ryzen and EPYC
- Apple M1, M2, M3, M4

### GPU

- NVIDIA — via NVML ( `pip install ecotrace[gpu]` )
- AMD and Intel — via WMI on Windows
- Fallback TDP estimation when drivers are unavailable

### RAM

- DDR4 and DDR5 (auto-detected from system profile)
- Estimation model: 0.375 W per GB

---

## CLI Reference

| Command | Description |
| --- | --- |
| `ecotrace run <script.py>` | Profile a script without modifying it |
| `ecotrace gate --budget <gCO2>` | Exit code 1 if accumulated emissions exceed budget |
| `ecotrace analyze <log.csv>` | Analyze a saved CSV emission log |
| `ecotrace export <log.csv>` | Export log to JSON |
| `ecotrace benchmark` | Run a standard CPU benchmark and report emissions |

---

## Region Code Reference

Pass the ISO 3166-1 alpha-2 code as `region_code` when initializing EcoTrace:

```
eco = EcoTrace(region_code="DE")
```

If the code is unrecognized, EcoTrace defaults to `GLOBAL` (475 gCO2/kWh). To use live data, pass a `grid_api_key` alongside the region code.
