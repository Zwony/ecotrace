from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from ..logger import logger
from ..tracker import EmissionsTracker

if TYPE_CHECKING:
    from transformers import TrainerCallback
else:
    try:
        from transformers import TrainerCallback
    except ImportError:
        class TrainerCallback:
            pass


class EcoTraceCallback(TrainerCallback):
    """Hugging Face Transformers TrainerCallback for carbon and energy tracking.

    Automatically hooks into `transformers.Trainer` lifecycle events to measure
    hardware energy consumption, inject emission metrics into training logs,
    and persist results to the audit trail.
    """

    def __init__(
        self,
        model_name: str = "HuggingFace Model",
        project_name: str | None = None,
        country_iso_code: str | None = None,
        region: str | None = None,
        output_dir: str | None = None,
        output_file: str | None = None,
        verbose: bool = True,
        **kwargs: Any,
    ) -> None:
        self.model_name = project_name or model_name
        self.verbose = verbose
        self.output_dir = output_dir
        self.output_file = output_file

        self._tracker = EmissionsTracker(
            project_name=self.model_name,
            country_iso_code=country_iso_code,
            region=region,
            output_dir=output_dir,
            output_file=output_file,
            **kwargs,
        )

        self._is_training = False
        self._epoch_start_time: float | None = None
        self._epoch_records: list[dict[str, Any]] = []
        self.total_emissions_kg: float = 0.0
        self.total_emissions_g: float = 0.0

    def on_train_begin(
        self,
        args: Any = None,
        state: Any = None,
        control: Any = None,
        **kwargs: Any,
    ) -> None:
        """Invoked when model training begins."""
        self._epoch_records.clear()
        self._tracker.start()
        self._is_training = True
        if self.verbose:
            logger.info(f"[EcoTrace] Training monitoring started for '{self.model_name}'.")

    def on_epoch_begin(
        self,
        args: Any = None,
        state: Any = None,
        control: Any = None,
        **kwargs: Any,
    ) -> None:
        """Invoked at the beginning of each training epoch."""
        self._epoch_start_time = time.perf_counter()

    def on_epoch_end(
        self,
        args: Any = None,
        state: Any = None,
        control: Any = None,
        **kwargs: Any,
    ) -> None:
        """Invoked at the conclusion of each training epoch."""
        now = time.perf_counter()
        epoch_idx = getattr(state, "epoch", len(self._epoch_records) + 1) if state else len(self._epoch_records) + 1
        epoch_duration = max(0.0001, now - (self._epoch_start_time or now))

        record = {
            "epoch": epoch_idx,
            "duration_s": epoch_duration,
        }
        self._epoch_records.append(record)

        if self.verbose:
            logger.info(f"[EcoTrace] Epoch {epoch_idx} completed in {epoch_duration:.2f}s.")

    def on_log(
        self,
        args: Any = None,
        state: Any = None,
        control: Any = None,
        logs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Injects carbon emission metrics into Trainer logs for dashboards like WandB/TensorBoard."""
        if logs is not None and isinstance(logs, dict):
            current_g = getattr(self._tracker._eco, "total_carbon", 0.0)
            logs["carbon_gco2"] = round(current_g, 6)
            logs["emissions_kg"] = round(current_g / 1000.0, 8)

    def on_train_end(
        self,
        args: Any = None,
        state: Any = None,
        control: Any = None,
        **kwargs: Any,
    ) -> None:
        """Invoked when model training concludes."""
        if not self._is_training:
            return

        self.total_emissions_kg = self._tracker.stop()
        self.total_emissions_g = self._tracker.final_emissions_g
        self._is_training = False

        if self.verbose:
            logger.info("=" * 50)
            logger.info(f"[EcoTrace] Training completed: {self.model_name}")
            logger.info(f"Total Duration : {self._tracker.duration_seconds:.2f}s")
            logger.info(f"Total Carbon   : {self.total_emissions_g:.6f} gCO2 ({self.total_emissions_kg:.8f} kgCO2)")
            logger.info("=" * 50)


EcoTraceTrainerCallback = EcoTraceCallback
EcoTraceHuggingFaceCallback = EcoTraceCallback
