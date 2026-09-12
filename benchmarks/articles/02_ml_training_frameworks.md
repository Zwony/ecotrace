# Quantitative Energy & Carbon Benchmark: PyTorch vs. TensorFlow on CNN Training

## Executive Summary

Deep learning frameworks are routinely compared by compute throughput (samples per second), time-to-convergence, and memory footprint. However, computational power consumption ($Wh$) and operational emissions ($gCO_2eq$) are critical dimensions for sustainable artificial intelligence.

In this benchmark, we evaluate the computational energy efficiency and carbon emissions of identical Convolutional Neural Network (CNN) architectures trained on the CIFAR-10 dataset using **PyTorch 2.x** and **TensorFlow 2.x / Keras**.

Telemetry is captured with microsecond resolution using **[EcoTrace](https://github.com/Zwony/ecotrace)**, leveraging continuous hardware sampling and dynamic grid carbon intensity modeling.

---

## 1. Test Architecture & Methodology

### Workload Specification
The workload trains a standard 3-layer convolutional neural network (LeNet-5 derivative) with dropout regularization and dense classification layers:
- **Dataset**: CIFAR-10 (50,000 training images, 10,000 validation images, 32x32x3 RGB).
- **Hyperparameters**: Batch size = 64, Optimizer = Adam ($\alpha = 10^{-3}$), Loss = Cross-Entropy, Epochs = 5.
- **Normalization**: Zero-mean and unit-variance normalization across color channels $(\mu = [0.4914, 0.4822, 0.4465], \sigma = [0.2470, 0.2435, 0.2616])$.

### Instrumentation Methodology
The benchmark utilizes `EcoTrace.track_block()` across isolated training executions with automated warm-up and statistical dispersion tracking:

```python
from ecotrace import EcoTrace

eco = EcoTrace(run_label="ML-Framework-Benchmark", check_updates=False)

with eco.track_block("pytorch_training"):
    train_pytorch_cnn(num_epochs=5, batch_size=64)

with eco.track_block("tensorflow_training"):
    train_tensorflow_cnn(num_epochs=5, batch_size=64)
```

### Hardware & Environment Specifications
* **CPU / Platform**: Modern Multi-Core x86_64 / ARM64 Host
* **GPU**: NVIDIA Tensor Core GPU / CUDA Accelerated (with CPU fallback validation)
* **Energy Sensor**: NVIDIA NVML Power Telemetry + Host CPU/RAM Instrumentation
* **Grid Region**: Dynamic / ISO-standard grid factor

---

## 2. Experimental Results & Analysis

### Energy and Emission Profiles

| Metric | PyTorch 2.x | TensorFlow 2.x | Efficiency Delta |
| :--- | :--- | :--- | :--- |
| **Mean Execution Time (5 Epochs)** | Baseline ($T_{PT}$) | $T_{TF}$ | Framework Overhead Comparison |
| **Total Energy Consumed ($Wh$)** | $E_{PT}$ | $E_{TF}$ | Hardware Draw |
| **Carbon Footprint ($gCO_2eq$)** | $C_{PT}$ | $C_{TF}$ | Direct Emissions |
| **Carbon per Accuracy Point ($gCO_2 / \%$)** | $C_{PT} / Acc$ | $C_{TF} / Acc$ | **Learning Carbon Efficiency** |
| **Statistical Significance ($p$-value)** | — | — | Mann-Whitney U ($p < 0.05$) |

*(Detailed run telemetry automatically exported to `benchmarks/results/02_ml_training_frameworks.json`)*

---

## 3. Engineering Insights: Computational Graph Dynamics

### A. Graph Execution Overhead vs. Eager Execution
PyTorch's imperative eager mode provides dynamic dispatch flexibility at runtime, whereas TensorFlow's XLA graph compilation and autograph caching can fuse CUDA kernels, leading to distinct thermal and power spikes during initialization followed by stabilized steady-state power draw.

### B. Memory Allocation & Host-to-Device Transfers
PyTorch caching allocators minimize host-device synchronization latency, decreasing CPU active-wait energy consumption during batch staging. TensorFlow's `tf.data` pipeline optimizes prefetching asynchronously across host threads, trading off marginal CPU power for sustained GPU tensor core saturation.

---

## 4. Reproducibility Guide

```bash
# Clone the repository
git clone https://github.com/Zwony/ecotrace.git
cd ecotrace/benchmarks

# Run the benchmark
python 02_ml_training_frameworks.py
```
