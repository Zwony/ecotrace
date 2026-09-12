# Spatial Arbitrage in Green Computing: Regional Grid Carbon Intensity

*The same workload, executed in different countries, produces dramatically different carbon footprints.*

> **Auto-generated from `benchmarks/results/*.json`** on 2026-09-01 21:40:15 UTC. Re-run `python benchmarks/report_generator.py` to refresh after new measurements.

---

## Executive Summary

Software efficiency is only half of the environmental equation. The geographic location where code executes determines the carbon intensity of the underlying electricity grid. Two identical servers running the identical workload can exhibit carbon footprint variations exceeding an order of magnitude depending on the regional energy mix.

This study benchmarks a deterministic, compute-intensive matrix-multiplication workload across **15 distinct international grid regions** using **EcoTrace**.

## 1. Methodology

- **Kernel**: Continuous dense floating-point matrix multiplication ($1500 \times 1500$ single-precision FP32)
- **Execution profile**: Deterministic fixed-duration execution (10.0 seconds per run), ensuring identical energy consumption ($Wh$) across all trials
- **Grid intensity source**: EcoTrace `constants.json` carbon intensity map

### Carbon Accounting Model

$$\text{Emissions } (gCO_2) = \frac{\text{Energy } (Wh)}{1000} \times \text{Grid Intensity } (gCO_2/kWh)$$

## 2. Empirical Results

### 2.1 Per-Region Carbon Footprint (sorted by grid intensity)

| Country | Code | Grid Intensity | Mean Energy (Wh) | Mean Carbon (gCO₂) | Relative vs. Cleanest |
| :-------- | --------: | --------: | --------: | --------: | --------: |
| Sweden | SE | 13 g/kWh | 0.088203 | 1.1 mg | 1.0x |
| Switzerland | CH | 25 g/kWh | 0.089618 | 2.2 mg | 2.0x |
| Norway | NO | 26 g/kWh | 0.088671 | 2.3 mg | 2.0x |
| France | FR | 55 g/kWh | 0.093369 | 5.1 mg | 4.5x |
| Brazil | BR | 74 g/kWh | 0.090054 | 6.7 mg | 5.8x |
| Canada | CA | 130 g/kWh | 0.090628 | 11.8 mg | 10.3x |
| United Kingdom | GB | 253 g/kWh | 0.090425 | 22.9 mg | 20.0x |
| United States | US | 367 g/kWh | 0.091424 | 33.6 mg | 29.3x |
| Germany | DE | 385 g/kWh | 0.089905 | 34.6 mg | 30.2x |
| Japan | JP | 463 g/kWh | 0.089242 | 41.3 mg | 36.0x |
| Türkiye | TR | 475 g/kWh | 0.090789 | 43.1 mg | 37.6x |
| China | CN | 555 g/kWh | 0.088763 | 49.3 mg | 43.0x |
| India | IN | 708 g/kWh | 0.090791 | 64.3 mg | 56.1x |
| Indonesia | ID | 761 g/kWh | 0.087971 | 66.9 mg | 58.4x |
| South Africa | ZA | 928 g/kWh | 0.090569 | 84.0 mg | 73.3x |

### 2.2 Headline Insight

The **same workload** in **South Africa (ZA)** produces **73× MORE** carbon than in **Sweden (SE)**.

**Region selection alone can reduce emissions by 99%** — without changing a single line of algorithmic code.

## 3. Engineering Implications

### A. Zero-Code Carbon Reductions

Without refactoring or modifying a single line of algorithmic code, migrating batch compute jobs (CI/CD test runners, model training, analytical batch queries) from carbon-intensive regions to low-carbon cloud datacenters (e.g. `us-east-1` $\to$ `eu-north-1`) achieves up to 98% immediate carbon reductions.

### B. Carbon-Aware Workload Scheduling

EcoTrace allows engineering systems to dynamically monitor regional carbon factors via static datasets or live real-time grid APIs (Electricity Maps integration), enabling automated dispatch decisions based on current grid marginal emissions.

## 4. Reproducibility

```bash
cd benchmarks
python 06_regional_carbon.py
python report_generator.py 06
```

Output JSON: `benchmarks/results/06_regional_carbon.json`

---

### Test Environment

- **CPU**: 13th Gen Intel(R) Core(TM) i7-13700H
- **Clock**: 2.9180 GHz
- **Cores**: 14 physical / 20 logical
- **Memory**: 15.65 GB
- **OS**: Windows 10
- **Python**: 3.11.1
- **Power source**: Battery
- **Run timestamp**: 2026-09-01T21:23:30.989384+00:00
- **Key packages**:
  - `ecotrace`: 1.5.1
  - `matplotlib`: 3.10.9
  - `numpy`: 2.4.6
  - `pandas`: 3.0.5
  - `polars`: 1.44.1
  - `psutil`: 7.2.2
  - `torch`: 2.11.0+cpu
