# EcoTrace Academic Benchmark Suite

Scientific, reproducible green computing benchmarks evaluating energy efficiency, operational carbon emissions ($gCO_2eq$), and hardware power scaling across diverse computing workloads.

---

##  Benchmark Index & Studies

| Study | Title | Category | Focus | Runner |
| :---: | :--- | :--- | :--- | :--- |
| **01** | [Pandas vs. Polars](articles/01_pandas_vs_polars.md) | Data Engineering | Vectorization, Arrow format, Race-to-Sleep | `python pandas_vs_polars.py` |
| **02** | [PyTorch vs. TensorFlow](articles/02_ml_training_frameworks.md) | Machine Learning | CNN Training on CIFAR-10, Carbon per Accuracy Point | `python 02_ml_training_frameworks.py` |
| **03** | [Sorting Algorithm Complexity](articles/03_sorting_algorithms.md) | Computer Science | $O(n \log n)$ vs $O(n^2)$ physical energy scaling | `python 03_sorting_algorithms.py` |
| **04** | [Web Framework Efficiency](articles/04_web_frameworks.md) | Cloud Systems | Flask vs FastAPI request carbon cost under load | `python 04_web_frameworks.py` |
| **05** | [LLM Inference Scaling](articles/05_llm_inference.md) | Generative AI | Per-token energy cost across GPT-2 parameter tiers | `python 05_llm_inference.py` |
| **06** | [Cross-Region Grid Variability](articles/06_regional_carbon.md) | Cloud Architecture | Up to 70x spatial carbon difference across 15 countries | `python 06_regional_carbon.py` |
| **07** | [Accuracy vs. RAPL](articles/07_accuracy_validation.md) | Energy Metrology | Model-vs-hardware validation (MAPE, MAE, R²) — Linux/RAPL for ground truth, synthetic fallback elsewhere | `python validation/accuracy_vs_rapl.py` |

---

##  Framework Architecture (`benchmarks/framework/`)

All studies in this suite leverage our reusable benchmarking framework:
- **`BenchmarkRunner`**: Standardized harness managing warm-up iterations, cooldown intervals, and automated EcoTrace telemetry collection.
- **`BenchmarkStatistics`**: Statistical aggregator providing 95% confidence intervals, IQR outlier rejection, and Mann-Whitney U hypothesis significance tests ($p < 0.05$).
- **`EnvironmentSnapshot`**: Captures hardware fingerprints (CPU, GPU, RAM, power state) and package dependency trees to ensure scientific reproducibility.

---

##  Quickstart

```bash
# 1. Install benchmark dependencies
pip install -r benchmarks/requirements.txt

# 2. Execute any benchmark
python benchmarks/03_sorting_algorithms.py

# 3. Results are saved to benchmarks/results/<study>.json

# 4. (Optional) Regenerate the article from the latest results
python benchmarks/report_generator.py 03
# Or regenerate all registered studies at once:
python benchmarks/report_generator.py
```

The report generator reads `benchmarks/results/*.json` and rewrites the corresponding article in `benchmarks/articles/*.md`. Run it after every benchmark to keep the published numbers in sync with the actual measurements.

---

##  Citation

If you use EcoTrace or these benchmarks in academic research, please cite:

```bibtex
@software{ozkal2026ecotrace,
  author = {Ozkal, Emre},
  title = {EcoTrace: High-Precision Energy and Emissions Instrumentation for Python},
  year = {2026},
  url = {https://github.com/Zwony/ecotrace},
  version = {1.5.0}
}
```
