# Hugging Face Transformers Integration

### Automatic Hardware Energy & Carbon Instrumentation for Model Training Loops

---

## Overview

EcoTrace provides a first-class `TrainerCallback` for the Hugging Face `transformers` ecosystem (`ecotrace.callbacks.huggingface`).

When attached to a Hugging Face `Trainer`, EcoTrace automatically:

- Hooks into `on_train_begin`, `on_epoch_begin`, `on_epoch_end`, `on_log`, and `on_train_end`.
- Measures continuous GPU (NVIDIA NVML) and CPU (RAPL) power consumption across training steps.
- Injects energy and carbon metrics directly into `state.log_history` for seamless integration with TensorBoard, Wandb, and MLflow.
- Outputs an audit-ready training carbon summary upon run completion.

---

## Installation

```bash
pip install ecotrace transformers datasets
```

For GPU tracking (recommended for training workloads):

```bash
pip install ecotrace[gpu]
```

---

## Quick Start

Import `EcoTraceCallback` (or `EcoTraceTrainerCallback`) and pass it to your `Trainer`:

```python
from transformers import AutoModelForSequenceClassification, Trainer, TrainingArguments
from ecotrace.callbacks import EcoTraceCallback

# 1. Initialize callback
eco_callback = EcoTraceCallback(
    model_name="bert-fine-tuning",
    country_iso_code="TR",  # Regional grid factor
)

# 2. Define standard training arguments
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    logging_steps=50,
)

# 3. Pass callback to Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    callbacks=[eco_callback],
)

# 4. Train model with real-time carbon instrumentation
trainer.train()

# 5. Access final metrics
print(f"Total Emissions: {eco_callback.total_emissions_g:.4f} gCO2")
```

---

## Configuration Options

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `model_name` | `str` | `"HuggingFace Model"` | Project identifier for telemetry tracking. |
| `country_iso_code` | `str` | Auto-detected | 2-letter ISO country code for grid carbon intensity. |
| `output_dir` | `str` | `None` | Directory path where session logs (`ecotrace_log.csv`) are written. |
| `verbose` | `bool` | `True` | Whether to print terminal summaries at the end of training. |

---

## Metrics Injected into Trainer Logs

During training, `EcoTraceCallback` enriches each logging step with:

- `emissions_g`: Grams of $CO_2$ emitted during the training window.
- `energy_kwh`: Total electricity consumed by CPU and active GPU accelerators.
- `cpu_power_w`: Estimated/measured processor package power.
- `gpu_power_w`: Hardware power draw across active NVIDIA accelerators.

