"""
PyTorch inference example with EcoTrace.

Runs batched forward passes through a small CNN and measures emissions two
ways: with the ``@track_emissions`` decorator and with the ``EmissionsTracker``
context manager. The model uses random weights and synthetic inputs, so the
script runs offline and needs no downloads.

Requires: torch
"""

from __future__ import annotations

import csv
import os
import sys
import tempfile

try:
    import torch
    from torch import nn
except ImportError:
    sys.exit("This example needs PyTorch. Install it with: pip install torch")

from ecotrace import EmissionsTracker, track_emissions

BATCH_SIZE = 32
NUM_BATCHES = 20
REGION = "GLOBAL"


def build_model() -> nn.Module:
    """Build a small CNN classifier with random weights."""
    model = nn.Sequential(
        nn.Conv2d(3, 16, kernel_size=3, padding=1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Conv2d(16, 32, kernel_size=3, padding=1),
        nn.ReLU(),
        nn.AdaptiveAvgPool2d(1),
        nn.Flatten(),
        nn.Linear(32, 10),
    )
    return model.eval()


def run_inference(model: nn.Module) -> int:
    """Run batched forward passes and return the number of samples processed."""
    generator = torch.Generator().manual_seed(0)
    samples = 0
    with torch.no_grad():
        for _ in range(NUM_BATCHES):
            batch = torch.randn(BATCH_SIZE, 3, 64, 64, generator=generator)
            model(batch).argmax(dim=1)
            samples += batch.shape[0]
    return samples


def print_summary(title: str, energy_kwh: float, duration_s: float, emissions_g: float) -> None:
    """Print energy, duration and emissions for one measurement."""
    print(f"\n{title}")
    print(f"  Energy   : {energy_kwh:.10f} kWh")
    print(f"  Duration : {duration_s:.4f} s")
    print(f"  Carbon   : {emissions_g:.8f} gCO2eq")


def main() -> None:
    """Measure the same inference workload with both tracking styles."""
    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
    model = build_model()

    # Context manager: the tracker object exposes the results directly.
    with EmissionsTracker(
        project_name="pytorch-inference-context",
        country_iso_code=REGION,
        save_to_file=False,
    ) as tracker:
        samples = run_inference(model)

    # The tracker reports gCO2eq but has no energy field, so kWh is derived:
    # energy (kWh) = gCO2eq / grid intensity (gCO2eq/kWh). The intensity is read from
    # the underlying EcoTrace object (an internal attribute, which may change).
    intensity = tracker._eco.carbon_intensity
    print_summary(
        f"Context manager ({samples} samples)",
        tracker.final_emissions_g / intensity,
        tracker.duration_seconds,
        tracker.final_emissions_g,
    )

    # Decorator: the wrapped function returns its own result, so the
    # measurement is read back from the CSV the decorator writes.
    with tempfile.TemporaryDirectory() as out_dir:

        @track_emissions(
            project_name="pytorch-inference-decorator",
            country_iso_code=REGION,
            output_dir=out_dir,
            output_file="emissions.csv",
        )
        def decorated_inference() -> int:
            return run_inference(model)

        samples = decorated_inference()
        duration_s, emissions_g = read_last_row(os.path.join(out_dir, "emissions.csv"))

    print_summary(
        f"Decorator ({samples} samples)",
        emissions_g / intensity,
        duration_s,
        emissions_g,
    )


def read_last_row(path: str) -> tuple[float, float]:
    """Return (duration_seconds, emissions_g) from the last row of a tracker CSV."""
    with open(path, newline="", encoding="utf-8") as f:
        row = list(csv.DictReader(f))[-1]
    return float(row["duration_seconds"]), float(row["emissions_g"])


if __name__ == "__main__":
    main()
