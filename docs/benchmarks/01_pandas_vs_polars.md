# Quantitative Energy & Carbon Benchmark: Pandas vs. Polars on Tabular Aggregations

## Executive Summary

While runtime latency and RAM allocation are standard metrics for comparing Python data manipulation frameworks, CPU package energy expenditure and operational carbon footprint ($gCO_2eq$) are rarely quantified.

In this benchmark, we evaluate the CPU power consumption, energy efficiency (Joules and Watt-hours), and estimated carbon intensity of identical data processing pipelines running on **Pandas 2.x** and **Polars 0.20+ (Lazy API)**. 

Telemetry is captured at high resolution using **[EcoTrace](https://github.com/Zwony/ecotrace)**, an open-source Python carbon and energy profiler that samples processor utilization against calibrated idle baselines.

---

## 1. Test Architecture & Methodology

### Workload Description
The workload simulates a typical analytical aggregation query on an e-commerce transaction dataset (2,000,000 to 5,000,000 records, Apache Parquet format):
1. **Ingestion**: Reading the dataset from disk.
2. **Predicate Filtering**: Multi-condition filtering (`country IN ('US', 'DE', 'GB') AND amount > 50.0`).
3. **Categorical GroupBy & Aggregation**: Computing categorical sums, arithmetic means, and counts across distinct product categories.
4. **Sorting**: Ordering aggregated results by total revenue in descending order.

### Instrumentation Architecture
The test uses `EcoTrace.track_block()` context managers to isolate each execution block:

```python
from ecotrace import EcoTrace

eco = EcoTrace(run_label="DataEngine-Benchmark", check_updates=False)

# Measure Pandas Pipeline
with eco.track_block("pandas_pipeline"):
    run_pandas_pipeline()

# Measure Polars Pipeline (Lazy API)
with eco.track_block("polars_pipeline"):
    run_polars_pipeline()
```

### Environment & Hardware Specifications
* **Processor**: 13th Gen Intel(R) Core(TM) i7-13700H (14 Cores / 20 Threads, 6 P-cores + 8 E-cores, up to 5.00 GHz)
* **Memory**: 16 GB DDR5 RAM
* **Operating System**: Microsoft Windows 11 Pro (64-bit, AC Powered)
* **Python Runtime**: CPython 3.11.1
* **Engine Versions**: Pandas 3.0.5 (PyArrow backend) vs. Polars 1.44.1 (Lazy API)

---

## 2. Benchmark Results

*Live Telemetry from EcoTrace Engine (`ecotrace_log.csv`)*

| Metric | Pandas 3.0.5 (PyArrow) | Polars 1.44.1 (Lazy) | Efficiency Gain |
| :--- | :--- | :--- | :--- |
| **Execution Duration** | `0.7011 s` | `0.1010 s` | **6.94x Speedup** |
| **Average System CPU Utilization\*** | `3.40%` | `6.67%` | **Parallel multi-thread burst** |
| **Carbon Footprint ($gCO_2eq$)** | `0.002201 g` | `0.000357 g` | **-83.8% Emissions** |
| **Net Carbon Saved / Run** | — | — | **0.001844 g $CO_2eq$** |

![EcoTrace Benchmark Chart](../assets/pandas_vs_polars_benchmark.png)

*\*Note on CPU Utilization: EcoTrace samples whole-system processor utilization at 50 ms intervals normalized across all 20 logical threads. Because Polars completes the entire computation in an ultra-fast burst (~100 ms) across multiple threads before returning to idle, the time-averaged whole-system percentage registers at 6.67% (representing nearly 2x higher parallel thread activity than Pandas during its active window).*

---

## 3. Engineering Analysis: Why Polars Consumes Less Energy

### A. The "Race-to-Sleep" Hardware Phenomenon
Modern multi-core processors implement power management C-states. When an execution thread occupies a core for extended durations, the CPU package remains in an active high-power state. 

Polars engages multi-threaded execution across all available logical cores via Rust's Rayon pool. By completing the computation in ~100 ms, the processor quickly drops back into low-power idle states, drastically reducing cumulative energy expenditure.

### B. Predicate Pushdown & Memory Bandwidth
Polars' lazy query planner analyzes the query graph and applies column projection and filter pushdowns directly to the Parquet reader. Unused columns and non-matching row groups are never materialized into memory, reducing DRAM bus activation.

### C. Vectorized Memory Layout (Apache Arrow)
Apache Arrow data structures maintain contiguous memory layouts, maximizing L1/L2/L3 cache hit rates and enabling SIMD (Single Instruction, Multiple Data) vectorization. Fewer memory stalls translate directly to lower Watts consumed per million rows processed.

---

## 4. Macro-Scale Multiplier Effect

In cloud environments (AWS, GCP, Azure), data engineering pipelines run on continuous recurring schedules:

* **Medium Enterprise (100,000 daily pipeline executions):**
  * Annual Carbon Avoided: **~67.3 kg $CO_2eq$**
  * Equivalent to driving an average gasoline vehicle over 280 km less each year.

* **Hyperscale Fleet (10,000,000 daily analytical queries):**
  * Annual Carbon Avoided: **~6.73 Metric Tons of $CO_2eq$**
  * Equivalent Environmental Benefit: **Sequestration capacity of 300+ mature trees annually**.

---

## 5. How to Audit Your Own Code with EcoTrace

EcoTrace allows measuring function-level and block-level energy consumption and carbon emissions in production and local environments.

### Installation
```bash
pip install ecotrace
```

### Usage Example
```python
from ecotrace import EcoTrace

eco = EcoTrace(run_label="MyDataPipeline")

@eco.track
def transform_data():
    # Your transformation logic
    pass

transform_data()
```

### Reproduce This Benchmark
The full benchmark script and dataset generator are open-source:

```bash
git clone https://github.com/Zwony/ecotrace.git
cd ecotrace/benchmarks
python pandas_vs_polars.py
```

* **Repository**: [https://github.com/Zwony/ecotrace](https://github.com/Zwony/ecotrace)
* **Official Website**: [https://ecotracelibrary.com](https://ecotracelibrary.com)
* **Documentation**: [https://ecotrace.readthedocs.io/](https://ecotrace.readthedocs.io/)
