# Advanced Usage Guide

## Detailed API

### `@eco.track_gpu` — GPU Monitoring
Supports **NVIDIA, AMD, and Intel GPUs** with real-time utilization sampling.

```python
eco = EcoTrace(gpu_index=0)

@eco.track_gpu
def gpu_inference():
    pass
```

### `eco.compare()` — Performance Analysis
```python
result = eco.compare(bubble_sort, quick_sort)
```

### `eco.track_block()` — Context Manager
```python
with eco.track_block("data_pipeline"):
    process_data()
```

---

## Integrations

### Live Grid API (Electricity Maps)
Fetch **real-time carbon intensity** data:

```python
eco = EcoTrace(region_code="DE", grid_api_key="YOUR_KEY")
```

### Gemini AI Insights
Generate actionable optimization advice:

```python
eco = EcoTrace(api_key="YOUR_GEMINI_API_KEY")
eco.generate_pdf_report("smart_audit.pdf")
```
- **Vectorization advice**: Detects loops that could be NumPy arrays.
- **Architecture tuning**: Suggests `asyncio` for I/O bound tasks.

---

## Benchmarks

### 1. Lightweight Workload
- **CPU Utilization:** `4.8%`
- **Carbon Footprint:** `0.000574 gCO₂`

### 2. Heavyweight Workload (20-Core Stress)
- **CPU Utilization:** `77.0%`
- **Carbon Footprint:** `0.414649 gCO₂`
