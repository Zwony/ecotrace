# Per-Token Carbon Economics: Quantifying Energy Scaling Laws in LLM Inference

## Executive Summary

As Large Language Models (LLMs) proliferate across production applications, inference costs have surpassed training costs in aggregate lifecycle energy consumption. Understanding the relationship between model parameter scale ($N_{\text{params}}$) and per-token operational emissions ($gCO_2 / 1\text{k tokens}$) is vital for responsible AI deployment.

This study benchmarks autoregressive transformer generation across the GPT-2 architecture family (**GPT-2 Small 124M**, **GPT-2 Medium 355M**, and **GPT-2 Large 774M**) using **EcoTrace**.

---

## 1. Experimental Methodology

### Model Architectures Under Test
1. **GPT-2 Small**: 124 Million Parameters, 12 layers, 12 attention heads, 768 hidden dimension.
2. **GPT-2 Medium**: 355 Million Parameters, 24 layers, 16 attention heads, 1024 hidden dimension.
3. **GPT-2 Large**: 774 Million Parameters, 36 layers, 20 attention heads, 1280 hidden dimension.

### Workload & Sampling Design
- Standardized prompt suite evaluating factual and analytical generation (5 prompts, greedy decoding, 50 new tokens per prompt).
- Per-batch GPU power integration sampled via NVML and EcoTrace high-frequency power estimation.
- Metrics normalized per 1,000 generated tokens:

$$\text{Carbon}_{\text{1k tokens}} = \frac{\text{Emissions}_{\text{total}}}{\text{Tokens}_{\text{total}}} \times 1000$$

---

## 2. Experimental Results & Scaling Characteristics

| Model Variant | Parameters | Generation Latency ($s$) | Throughput (Tokens/s) | Carbon ($gCO_2 / 1\text{k tokens}$) | Scale Multiplier |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GPT-2 Small** | 124M | $T_{\text{Small}}$ | $\text{Tok/s}_{\text{Small}}$ | $C_{\text{Small}}$ | **1.0x (Baseline)** |
| **GPT-2 Medium** | 355M | $T_{\text{Medium}}$ | $\text{Tok/s}_{\text{Medium}}$ | $C_{\text{Medium}}$ | **~2.8x Parameters** |
| **GPT-2 Large** | 774M | $T_{\text{Large}}$ | $\text{Tok/s}_{\text{Large}}$ | $C_{\text{Large}}$ | **~6.2x Parameters** |

---

## 3. Engineering Insights: The Memory Bandwidth Bottleneck

### A. KV-Cache Memory Traffic
In autoregressive text generation, the key-value cache access on every sequential step causes memory-bandwidth-bound operation rather than compute-bound operation. Larger model dimensions require fetching larger parameter tensors from VRAM for each generated token, driving memory controller power.

### B. Optimal Parameter Selection for Task Complexity
Deploying an oversized model for basic classification or extraction tasks represents significant carbon wastage. Using EcoTrace's per-token emission instrumentation, engineering teams can implement carbon-budget-aware routing (e.g. routing simple queries to 124M-scale models and complex queries to larger tiers).

---

## 4. Reproduction

```bash
cd ecotrace/benchmarks
python 05_llm_inference.py
```
