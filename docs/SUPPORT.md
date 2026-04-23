# Support & Reference

## Troubleshooting

- **Permission Denied (`psutil.AccessDenied`):** Run with higher privileges or ignore if child process tracking is not needed.
- **Missing Drivers (NVIDIA/WMI):** EcoTrace will fallback to CPU-only monitoring gracefully.
- **NoSuchProcess Error:** Usually occurs with extremely short-lived processes; samples are safely discarded.

---

## Data & Privacy
EcoTrace is **local-first**. Data is only sent to external APIs if specifically enabled (Live Grid, Gemini, Update Check).

---

## Global Coverage (50+ Countries)

EcoTrace supports 50+ countries with static IEA 2024 averages and live zone mappings.

| Code | Country | gCO₂/kWh | | Code | Country | gCO₂/kWh |
|------|---------|----------:|-|------|---------|----------:|
| SE | Sweden | 13 | | US | United States | 367 |
| NO | Norway | 26 | | DE | Germany | 385 |
| FR | France | 55 | | TR | Turkey | 475 |
| CA | Canada | 130 | | IN | India | 708 |

---

## Supported Hardware

- **CPU:** Intel (Core/Xeon), AMD (Ryzen/EPYC), Apple (M1/M2/M3/M4).
- **GPU:** NVIDIA (NVML), AMD/Intel (WMI/Windows).
- **RAM:** DDR4, DDR5 auto-detection.
