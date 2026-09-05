# Carbon Cost of Serving: Web Framework Throughput vs. Energy per Request

*Comparing fastapi, flask under identical synthetic HTTP load.*

> **Auto-generated from `benchmarks/results/*.json`** on 2026-09-05 13:17:32 UTC. Re-run `python benchmarks/report_generator.py` to refresh after new measurements.

---

## Executive Summary

Different Python web frameworks have measurably different energy profiles per request under identical load. This study benchmarks the carbon cost of serving a simple JSON endpoint under a synthetic concurrent workload.

## 1. Methodology

- **Workload**: Simple JSON API endpoint returning a fixed payload (20 items)
- **Concurrent requests per run**: 10
- **Total requests per run**: 5000
- **Measured runs per framework**: 3
- **Load generator**: Python `urllib` with `ThreadPoolExecutor`

## 2. Results

| Framework | Mean Duration (s) | Mean Carbon (gCO2) | Req/s (mean) | p50 Latency (ms) | p99 Latency (ms) |
| :-------- | --------: | --------: | --------: | --------: | --------: |
| FLASK | 18.9725 s [15.3755 s, 22.5695 s] | 74.8 mg [59.7 mg, 89.9 mg] | 265 | 35.2 | 97.2 |
| FASTAPI | 22.5036 s [17.8062 s, 27.2009 s] | 81.5 mg [59.9 mg, 103.1 mg] | 199 | 46.0 | 162.0 |

## 3. Pairwise Comparison

- **Baseline**: flask
- **Challenger**: fastapi
- **Speedup ratio**: 0.84x
- **Carbon reduction**: -8.9%
- **Statistical significance (duration)**: NO (p = 0.1266)

## 4. Reproducibility

```bash
cd benchmarks
python 04_web_frameworks.py
python report_generator.py 04
```

Output JSON: `benchmarks/results/04_web_frameworks.json`

---

### Test Environment

- **CPU**: 13th Gen Intel(R) Core(TM) i7-13700H
- **Clock**: 2.9180 GHz
- **Cores**: 14 physical / 20 logical
- **Memory**: 15.65 GB
- **OS**: Windows 10
- **Python**: 3.11.1
- **Power source**: AC
- **Run timestamp**: 2026-09-05T13:14:07.699185+00:00
- **Key packages**:
  - `ecotrace`: 1.5.1
  - `fastapi`: 0.111.0
  - `flask`: 3.1.0
  - `matplotlib`: 3.10.9
  - `numpy`: 2.4.6
  - `pandas`: 3.0.5
  - `polars`: 1.44.1
  - `psutil`: 7.2.2
  - `torch`: 2.13.0+cpu
  - `uvicorn`: 0.30.1
