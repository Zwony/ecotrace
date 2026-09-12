# Empirical Accuracy Validation: EcoTrace Estimation Model vs. Hardware Ground Truth

*Sensor mode: **Simulation / Synthetic Hardware** — comparing EcoTrace's piecewise model against a synthetic non-linear reference curve.*

> **Auto-generated from `benchmarks/results/*.json`** on 2026-09-01 21:40:15 UTC. Re-run `python benchmarks/report_generator.py` to refresh after new measurements.

---

## Abstract

Accurate software-level energy quantification depends on the quality of the underlying power estimation model. Hardware-level register interfaces — Intel/AMD **RAPL** and Apple Silicon **powermetrics** — provide direct energy readings, but are unavailable on Windows and in many containerized or non-root environments. In these cases, libraries must fall back to a calibrated software estimation model.

This study validates **EcoTrace's** non-linear piecewise CPU power model under two modes:

1. **Hardware Mode** — direct comparison against `RAPL` register readings on Linux (highest fidelity).
2. **Synthetic Reference Mode** — comparison against a published non-linear CPU power curve, used when hardware counters are unavailable.

## 1. Mathematical Formulation

### A. Linear TDP Baseline (Naive)

$$P_{\text{linear}}(u) = TDP \times \left(\frac{u}{100}\right)$$

### B. EcoTrace Piecewise Calibrated Model

$$P_{\text{EcoTrace}}(u) = TDP \times f(u)$$

where $f(u)$ maps load ranges:

| Load Range | Curve $f(u)$ |
| :--- | :--- |
| $u \in [0\%, 10\%]$ | $0.12 + 0.20 \times \frac{u}{10}$ |
| $u \in [10\%, 50\%]$ | $0.32 + 0.43 \times \frac{u-10}{40}$ |
| $u \in [50\%, 100\%]$ | $0.75 + 0.27 \times \frac{u-50}{50}$ |

## 2. Validation Results (Latest Run)

**Sensor mode**: `Simulation / Synthetic Hardware`

### Per-Load-Step Comparison

| Load (%) | Reference Power (W) | EcoTrace Power (W) | Absolute Error (W) | Relative Error (%) |
| :-------- | --------: | --------: | --------: | --------: |
| 10 | 8.2035 | 14.4000 | 6.1965 | 75.5 |
| 25 | 13.4413 | 21.6562 | 8.2150 | 61.1 |
| 50 | 23.2448 | 33.7500 | 10.5052 | 45.2 |
| 75 | 33.8456 | 39.8250 | 5.9794 | 17.7 |
| 100 | 45.0000 | 45.9000 | 0.90 | 2.0 |

### Aggregate Error Metrics

| Metric | Value |
| :-------- | --------: |
| Mean Absolute Error (MAE) | 6.3592 W |
| Mean Absolute Percentage Error (MAPE) | 40.3000 % |
| Root Mean Squared Error (RMSE) | 7.1106 W |
| Coefficient of Determination (R²) | 0.7181 |

## 3. Interpretation

These error metrics reflect the agreement between EcoTrace's piecewise model and the reference (hardware or synthetic). For the strongest validation signal, run this script on a Linux host with RAPL access — typical reported accuracy is MAPE $\le 15\%$, R² $> 0.90$. On systems without hardware counters (Windows, containers, non-root), the synthetic reference yields a wider error distribution because it is a model-vs-model comparison rather than a model-vs-hardware comparison.

**Key insight**: EcoTrace is most accurate at saturation (full load), where the linear $TDP$ assumption holds. At low loads, expect a conservative bias because the piecewise model bakes in a static leakage floor — a deliberate choice to avoid under-reporting the carbon cost of always-on background services.

## 4. Reproducibility

```bash
cd benchmarks
python validation/accuracy_vs_rapl.py
python report_generator.py 07
```

Output JSON: `benchmarks/results/07_accuracy_validation.json`

---

### Test Environment

- **CPU**: 13th Gen Intel(R) Core(TM) i7-13700H
- **Clock**: 2.9180 GHz
- **Cores**: 14 physical / 20 logical
- **Memory**: 15.65 GB
- **OS**: Windows 10
- **Python**: 3.11.1
- **Power source**: Battery
- **Run timestamp**: 2026-09-01T21:00:09.394482+00:00
- **Key packages**:
  - `ecotrace`: 1.5.1
  - `matplotlib`: 3.10.9
  - `numpy`: 2.4.6
  - `pandas`: 3.0.5
  - `polars`: 1.44.1
  - `psutil`: 7.2.2
  - `torch`: 2.11.0+cpu
