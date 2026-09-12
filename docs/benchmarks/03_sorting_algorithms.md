# Algorithmic Complexity vs. Carbon Expenditure: The Empirical Energy Footprint of Sorting

*Cross-scale comparison of $O(n \log n)$ and $O(n^2)$ sorting algorithms on $N = 5 \times 10^4$ to $10^6$ random integers.*

> **Auto-generated from `benchmarks/results/*.json`** on 2026-09-05 13:10:08 UTC. Re-run `python benchmarks/report_generator.py` to refresh after new measurements.

---

## Executive Summary

Asymptotic computational complexity ($O(n \log n)$ vs. $O(n^2)$) forms the bedrock of computer science. This study systematically measures the **carbon cost** of this theoretical distinction by running five sorting algorithms across four input sizes using **EcoTrace**.

## 1. Experimental Setup

### Algorithms Tested

| Algorithm | Complexity | Implementation | Practical Use |
| :--- | :--- | :--- | :--- |
| **Python Timsort** (`sorted()`) | $O(n \log n)$ | C, adaptive | Standard library default |
| **NumPy Introsort** (`np.sort`) | $O(n \log n)$ | C/Fortran | Vectorized arrays |
| **Merge Sort** (pure Python) | $O(n \log n)$ | Python, recursive | Stable, educational |
| **Heap Sort** (`heapq`) | $O(n \log n)$ | Python, in-place | Memory-bounded |
| **Insertion Sort** (pure Python) | $O(n^2)$ | Python, simple | Small N, nearly-sorted data |

### Configuration

- **Scales tested**: 50,000, 100,000, 500,000, 1,000,000
- **Measured runs per scale**: 3
- **Random seed**: 42 (reproducible)

### Measurement Method

```python
from ecotrace import EcoTrace
eco = EcoTrace(run_label="Sorting-Benchmark", check_updates=False)

with eco.track_block(f"{algo}_{scale}_run_{i}"):
    sorted_array = algorithm(data)
```

Outliers filtered using the IQR rule (1.5x). Reported values are post-filter means with 95% confidence intervals.

## 2. Empirical Results

### 2.1 Wall-Clock Duration (mean, 95% CI interval)

| Algorithm | Complexity | $N = 50,000$ | $N = 100,000$ | $N = 500,000$ | $N = 1,000,000$ |
| :-------- | --------: | --------: | --------: | --------: | --------: |
| Python Timsort | $O(n \log n)$ | 8.21 ms [6.81 ms, 9.60 ms] | 18.99 ms [13.29 ms, 24.68 ms] | 115.10 ms [98.67 ms, 131.53 ms] | 237.43 ms [231.00 ms, 243.86 ms] |
| NumPy Introsort | $O(n \log n)$ | 3.57 ms [0.28 ms, 6.85 ms] | 6.80 ms [1.79 ms, 11.81 ms] | 29.84 ms [21.36 ms, 38.32 ms] | 59.06 ms [35.87 ms, 82.25 ms] |
| Merge Sort (Python) | $O(n \log n)$ | 120.45 ms [106.73 ms, 134.18 ms] | 247.61 ms [222.41 ms, 272.81 ms] | 1.5084 s [1.4686 s, 1.5482 s] | 3.2014 s [3.0051 s, 3.3976 s] |
| Heap Sort (Python) | $O(n \log n)$ | 18.27 ms [15.97 ms, 20.57 ms] | 38.63 ms [35.68 ms, 41.58 ms] | 435.75 ms [268.40 ms, 603.11 ms] | 1.3695 s [-101.62 ms, 2.8406 s] |
| Insertion Sort (Python) | $O(n^2)$ | 44.7573 s [41.4513 s, 48.0633 s] | -- | -- | -- |

### 2.2 Carbon Footprint (mean gCO2eq per run)

Grid region used: **GLOBAL (see `ecotrace.constants.json` for grid intensity)**.

| Algorithm | Complexity | $N = 50,000$ | $N = 100,000$ | $N = 500,000$ | $N = 1,000,000$ |
| :-------- | --------: | --------: | --------: | --------: | --------: |
| Python Timsort | $O(n \log n)$ | 0.15 mg [0.14 mg, 0.16 mg] | 0.16 mg [0.14 mg, 0.18 mg] | 1.4 mg [-2.47 mg, 5.3 mg] | 0.88 mg [0.74 mg, 1.0 mg] |
| NumPy Introsort | $O(n \log n)$ | 0.15 mg [0.15 mg, 0.16 mg] | 0.15 mg [0.14 mg, 0.16 mg] | 0.16 mg [0.15 mg, 0.16 mg] | 0.32 mg [0.30 mg, 0.34 mg] |
| Merge Sort (Python) | $O(n \log n)$ | 0.49 mg [0.47 mg, 0.50 mg] | 0.88 mg [0.63 mg, 1.1 mg] | 5.1 mg [4.8 mg, 5.3 mg] | 10.7 mg [10.1 mg, 11.3 mg] |
| Heap Sort (Python) | $O(n \log n)$ | 0.16 mg [0.16 mg, 0.16 mg] | 0.17 mg [0.16 mg, 0.18 mg] | 1.5 mg [1.0 mg, 2.0 mg] | 4.6 mg [-0.24 mg, 9.4 mg] |
| Insertion Sort (Python) | $O(n^2)$ | 148.1 mg [137.5 mg, 158.7 mg] | -- | -- | -- |

### 2.3 Headline Numbers

At $N = 1,000,000$, the C-backed **NumPy Introsort** produces **0.32 mg** of carbon per run, while the C-backed **Python Timsort** produces **0.88 mg** -- a 2.7x difference driven by vectorization and SIMD utilization in NumPy's implementation.

**Insertion Sort** (the only $O(n^2)$ contender) was run only at $N = 50,000$ because larger inputs become infeasible in pure Python. At that scale it consumed **148.1 mg** of carbon in **44.7573 s** -- **961x more carbon than NumPy Introsort on the same input**. This is the **quadratic carbon cliff**: the $O(n^2)$ penalty is not a linear slowdown, it is a catastrophic carbon explosion.

## 3. Engineering Insights

### A. The C/Native vs. Interpreted Energy Multiplier

Native C implementations (NumPy / CPython core) outperform pure Python equivalents by orders of magnitude not solely in latency, but in **energy per sorted record**. By avoiding bytecode evaluation loops and pointer dereferencing, native loops maximize CPU vector registers (SIMD) and instruction-level parallelism (ILP).

### B. Memory Allocation Tax

Algorithms with heavy object instantiation (Python recursive Merge Sort) generate extensive garbage collection overhead and DRAM read/write traffic. The memory controller and DRAM chips contribute a substantial fixed power draw ($P_{\text{DRAM}} \approx 0.375$ W/GB), penalizing high-allocation algorithms regardless of CPU speed. Heap Sort is more memory-friendly because it sorts in-place.

### C. The Quadratic Carbon Cliff

$O(n^2)$ algorithms don't just slow down linearly -- they explode. Insertion Sort's measured cost at $N = 50{,}000$ is already competitive with the slower $O(n \log n)$ algorithms; at $N = 10^6$ it would consume hours of CPU time and produce thousands of times more carbon. **Algorithmic choice is a carbon decision, not just a latency decision.**

## 4. Reproducibility

```bash
cd benchmarks
python 03_sorting_algorithms.py
python report_generator.py 03
```

Output JSON: `benchmarks/results/03_sorting_algorithms.json`

---

### Test Environment

- **CPU**: 13th Gen Intel(R) Core(TM) i7-13700H
- **Clock**: 2.9180 GHz
- **Cores**: 14 physical / 20 logical
- **Memory**: 15.65 GB
- **OS**: Windows 10
- **Python**: 3.11.1
- **Power source**: AC
- **Run timestamp**: 2026-09-05T13:05:53.539221+00:00
- **Key packages**:
  - `ecotrace`: 1.5.1
  - `matplotlib`: 3.10.9
  - `numpy`: 2.4.6
  - `pandas`: 3.0.5
  - `polars`: 1.44.1
  - `psutil`: 7.2.2
  - `torch`: 2.13.0+cpu
