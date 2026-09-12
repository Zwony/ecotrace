"""EcoTrace Keras/TensorFlow callback — per-epoch carbon tracking.

Integrates with ``model.fit()`` via the standard ``tf.keras.callbacks.Callback``
interface. TensorFlow is imported lazily — this module is safe to import
without TF installed; it only fails at instantiation time if TF is missing.

Example::

    from ecotrace.callbacks.keras import EcoTraceKerasCallback

    model.fit(
        x_train, y_train,
        epochs=10,
        callbacks=[EcoTraceKerasCallback(model_name="BERT-base")],
    )
"""

from typing import Optional, List, Tuple
import time
from ecotrace.ml import EcoTraceML


def _require_keras():
    """Deferred import of tf.keras.callbacks.Callback.

    Raises a clear ImportError with install instructions if TF is absent,
    instead of the cryptic ModuleNotFoundError that would surface at class
    definition time if we imported at the top level.
    """
    try:
        from tensorflow.keras.callbacks import Callback  # type: ignore
        return Callback
    except ImportError:
        raise ImportError(
            "EcoTraceKerasCallback requires TensorFlow. "
            "Install it with: pip install ecotrace[keras]"
        )


class EcoTraceKerasCallback:
    """Per-epoch carbon and energy tracker for Keras ``model.fit()`` loops.

    Implements the same interface as ``tf.keras.callbacks.Callback`` via
    duck-typing so it can be passed to ``model.fit(callbacks=[...])`` without
    TensorFlow being imported at EcoTrace import time.

    Under the hood this wraps :class:`~ecotrace.ml.EcoTraceML`, reading an
    energy snapshot at the start and end of every epoch to isolate per-epoch
    GPU energy consumption.

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
        model_name: str = "Keras Model",
        gpu_index: int = 0,
        sample_interval: float = 1.0,
        project_name: Optional[str] = None,
        epochs: Optional[int] = None,
        batch_size: Optional[int] = None,
        dataset_size: Optional[int] = None,
        verbose: bool = True,
    ):
        # Validate that Keras is available at construction time, not at import
        # time, so users get a friendly error rather than an attribute lookup
        # crash inside model.fit().
        _require_keras()

        self.model_name = project_name or model_name
        self.gpu_index = gpu_index
        self.sample_interval = sample_interval
        self.epochs = epochs
        self.batch_size = batch_size
        self.dataset_size = dataset_size
        self.verbose = verbose

        self._tracker: Optional[EcoTraceML] = None
        self._epoch_start_time: Optional[float] = None
        self._epoch_start_energy_j: float = 0.0
        self._epoch_results: List[Tuple[int, float, float]] = []

        # Keras needs these attributes to recognise a valid callback object
        self.params = {}
        self.model = None

    def set_params(self, params):
        """Called by Keras before training. Receives training parameters."""
        self.params = params

    def set_model(self, model):
        """Called by Keras before training. Receives the model being trained."""
        self.model = model

    def on_train_begin(self, logs=None):
        """Initialises the EcoTraceML tracker and starts GPU monitoring."""
        self._tracker = EcoTraceML(
            model_name=self.model_name,
            gpu_index=self.gpu_index,
            sample_interval=self.sample_interval,
            epochs=self.epochs,
            batch_size=self.batch_size,
            dataset_size=self.dataset_size,
        )
        self._tracker.__enter__()
        if self.verbose:
            gpu_brand = (self._tracker.gpu_info or {}).get("brand", "Unknown GPU")
            print(f"[EcoTrace] Keras training started — {self.model_name} on {gpu_brand}")

    def on_epoch_begin(self, epoch, logs=None):
        """Records the energy baseline at the start of each epoch."""
        if self._tracker is None:
            return
        energy_j, _ = self._tracker.snapshot_energy()
        self._epoch_start_energy_j = energy_j
        self._epoch_start_time = time.perf_counter()

    def on_epoch_end(self, epoch, logs=None):
        """Logs per-epoch carbon to CSV and optionally prints a summary.

        Args:
            epoch: Current epoch index (0-based, provided by Keras).
            logs: Keras metrics dict (e.g. ``{"loss": 0.42, "val_loss": 0.51}``).
        """
        if self._tracker is None or self._epoch_start_time is None:
            return

        epoch_duration = time.perf_counter() - self._epoch_start_time
        current_energy_j, _ = self._tracker.snapshot_energy()
        epoch_energy_j = max(0.0, current_energy_j - self._epoch_start_energy_j)

        # Pass Keras logs as metrics so loss appears in the CSV label
        metrics = dict(logs) if logs else {}
        carbon_g = self._tracker.log_epoch(epoch, epoch_energy_j, epoch_duration, metrics)

        self._epoch_results.append((epoch, carbon_g, epoch_duration))

        if self.verbose:
            loss_str = f" | loss={metrics['loss']:.4f}" if "loss" in metrics else ""
            print(
                f"[EcoTrace] Epoch {epoch:>3} — "
                f"{epoch_duration:.1f}s | "
                f"{carbon_g:.6f} gCO2{loss_str}"
            )

    def on_train_end(self, logs=None):
        """Exits the EcoTraceML context manager and prints the training summary."""
        if self._tracker is None:
            return
        self._tracker.__exit__(None, None, None)

        if self.verbose and self._epoch_results:
            total_carbon = sum(r[1] for r in self._epoch_results)
            worst_epoch, worst_carbon, _ = max(self._epoch_results, key=lambda r: r[1])
            print(f"\n[EcoTrace] Training complete — {len(self._epoch_results)} epochs")
            print(f"[EcoTrace] Total carbon    : {total_carbon:.6f} gCO2")
            print(f"[EcoTrace] Heaviest epoch  : Epoch {worst_epoch} ({worst_carbon:.6f} gCO2)")
