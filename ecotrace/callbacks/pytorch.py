"""EcoTrace PyTorch callback — per-epoch carbon tracking.

Works with any manual PyTorch training loop. Does NOT import ``torch``
at module level, so this file is safe to import in all environments.
``torch`` is only needed if you actually call ``on_epoch_begin/end``.

Example::

    from ecotrace.callbacks.pytorch import EcoTracePyTorchCallback

    cb = EcoTracePyTorchCallback(model_name="ResNet50", gpu_index=0)

    cb.on_train_begin()
    for epoch in range(num_epochs):
        cb.on_epoch_begin(epoch)
        train_one_epoch(model, dataloader, optimizer)
        val_loss = validate(model, val_loader)
        cb.on_epoch_end(epoch, metrics={"loss": val_loss})
    cb.on_train_end()
"""

import time
from ecotrace.ml import EcoTraceML


class EcoTracePyTorchCallback:
    """Per-epoch carbon and energy tracker for manual PyTorch training loops.

    Wraps :class:`~ecotrace.ml.EcoTraceML` to provide fine-grained, per-epoch
    carbon breakdowns — something the standard context manager cannot offer
    because it only records a single total at the end of training.

    This class has **zero mandatory dependencies beyond EcoTrace itself**.
    PyTorch is not imported at module or class level; you only need it
    installed if your training loop actually uses it (which it obviously does).

    Args:
        model_name: Human-readable name for the model/experiment.
        gpu_index: Zero-based GPU device index (default 0).
        sample_interval: GPU polling interval in seconds (default 1.0).
        project_name: Optional project label propagated to the run.
        epochs: Total planned epoch count (informational only).
        batch_size: Batch size (informational only).
        dataset_size: Dataset sample count (informational only).
        verbose: If True (default), prints per-epoch carbon summaries.
    """

    def __init__(
        self,
        model_name: str = "PyTorch Model",
        gpu_index: int = 0,
        sample_interval: float = 1.0,
        project_name: str = None,
        epochs: int = None,
        batch_size: int = None,
        dataset_size: int = None,
        verbose: bool = True,
    ):
        self.model_name = project_name or model_name
        self.gpu_index = gpu_index
        self.sample_interval = sample_interval
        self.epochs = epochs
        self.batch_size = batch_size
        self.dataset_size = dataset_size
        self.verbose = verbose

        self._tracker: EcoTraceML = None
        self._epoch_start_time: float = None
        self._epoch_start_energy_j: float = 0.0
        self._epoch_results: list = []  # [(epoch, carbon_g, duration_s)]

    def on_train_begin(self):
        """Called once before training starts. Initialises EcoTraceML and GPU monitor."""
        self._tracker = EcoTraceML(
            model_name=self.model_name,
            gpu_index=self.gpu_index,
            sample_interval=self.sample_interval,
            epochs=self.epochs,
            batch_size=self.batch_size,
            dataset_size=self.dataset_size,
        )
        # Enter the context manager manually so the monitoring thread runs
        # throughout the full training session.
        self._tracker.__enter__()
        if self.verbose:
            gpu_brand = (self._tracker.gpu_info or {}).get("brand", "Unknown GPU")
            print(f"[EcoTrace] Training started — {self.model_name} on {gpu_brand}")

    def on_epoch_begin(self, epoch: int):
        """Called at the start of each epoch. Records the energy baseline."""
        if self._tracker is None:
            raise RuntimeError("Call on_train_begin() before on_epoch_begin().")
        energy_j, _ = self._tracker.snapshot_energy()
        self._epoch_start_energy_j = energy_j
        self._epoch_start_time = time.perf_counter()

    def on_epoch_end(self, epoch: int, metrics: dict = None):
        """Called at the end of each epoch. Logs per-epoch carbon to CSV.

        Args:
            epoch: Current epoch index (0-based).
            metrics: Optional dict of training metrics, e.g. ``{"loss": 0.42}``.
        """
        if self._tracker is None or self._epoch_start_time is None:
            return

        epoch_duration = time.perf_counter() - self._epoch_start_time
        current_energy_j, _ = self._tracker.snapshot_energy()
        epoch_energy_j = max(0.0, current_energy_j - self._epoch_start_energy_j)

        self._tracker.log_epoch(epoch, epoch_energy_j, epoch_duration, metrics)

        # Carbon estimate for console output
        gpu_kwh = epoch_energy_j / 3_600_000.0
        raw_intensity = getattr(self._tracker.eco, "carbon_intensity", 0.475)
        carbon_g = (gpu_kwh * (raw_intensity * 1000.0 if raw_intensity < 10 else raw_intensity)) * 1.05

        self._epoch_results.append((epoch, carbon_g, epoch_duration))

        if self.verbose:
            loss_str = f" | loss={metrics['loss']:.4f}" if metrics and "loss" in metrics else ""
            print(
                f"[EcoTrace] Epoch {epoch:>3} — "
                f"{epoch_duration:.1f}s | "
                f"{carbon_g:.6f} gCO2{loss_str}"
            )

    def on_train_end(self):
        """Called once after training finishes. Prints summary and generates PDF report."""
        if self._tracker is None:
            return
        # Exit the context manager — this triggers the full session summary + PDF
        self._tracker.__exit__(None, None, None)

        if self.verbose and self._epoch_results:
            total_carbon = sum(r[1] for r in self._epoch_results)
            worst_epoch, worst_carbon, _ = max(self._epoch_results, key=lambda r: r[1])
            print(f"\n[EcoTrace] Training complete — {len(self._epoch_results)} epochs")
            print(f"[EcoTrace] Total carbon    : {total_carbon:.6f} gCO2")
            print(f"[EcoTrace] Heaviest epoch  : Epoch {worst_epoch} ({worst_carbon:.6f} gCO2)")
