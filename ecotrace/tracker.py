from __future__ import annotations

import asyncio
import csv
import functools
import inspect
import os
import time
from typing import Any, Callable, Dict, Optional, Union

from .core import EcoTrace



class EmissionsTracker:
    def __init__(
        self,
        project_name: str = "default",
        measure_power_secs: Optional[float] = None,
        output_dir: Optional[str] = None,
        output_file: Optional[str] = None,
        country_iso_code: Optional[str] = None,
        region: Optional[str] = None,
        save_to_file: bool = True,
        gpu_ids: Optional[Any] = None,
        log_level: Optional[str] = None,
        co2_signal_api_token: Optional[str] = None,
        tracking_mode: str = "process",
        **kwargs: Any,
    ) -> None:
        self.project_name = project_name
        self.output_dir = output_dir or "."
        self.output_file = output_file
        self.save_to_file = save_to_file
        self.region_code = country_iso_code or region or "GLOBAL"

        self._eco = EcoTrace(
            region_code=self.region_code,
            quiet=True,
            check_updates=False,
            session_summary=False,
            run_label=self.project_name,
        )

        self._is_active = False
        self._start_time: Optional[float] = None
        self._energy_start: Optional[float] = None
        self.final_emissions: float = 0.0
        self.final_emissions_g: float = 0.0
        self.duration_seconds: float = 0.0

    def start(self) -> None:
        if self._is_active:
            return
        self._start_time = time.perf_counter()
        self._energy_start = self._eco.hardware.get_cpu_energy_j()
        self._eco._start_cpu_monitor()
        if (hasattr(self._eco, "gpu_infos") and self._eco.gpu_infos) or self._eco.gpu_info:
            self._eco._start_gpu_monitor()
        self._is_active = True

    def stop(self) -> float:
        if not self._is_active or self._start_time is None:
            return self.final_emissions

        end_time = time.perf_counter()
        energy_end = self._eco.hardware.get_cpu_energy_j()
        duration = max(0.0001, end_time - self._start_time)
        self.duration_seconds = duration

        self._eco._stop_cpu_monitor()
        if (hasattr(self._eco, "gpu_infos") and self._eco.gpu_infos) or self._eco.gpu_info:
            self._eco._stop_gpu_monitor()

        self._is_active = False

        avg_cpu = self._eco._get_avg_cpu_in_range(self._start_time, end_time)
        energy_delta_j = None
        if self._energy_start is not None and energy_end is not None:
            energy_delta_j = max(0.0, energy_end - self._energy_start)

        cpu_carbon = self._eco._compute_carbon(
            self._eco.cpu_info["tdp"], avg_cpu, duration, energy_delta_j=energy_delta_j
        )

        gpu_carbon = 0.0
        if (hasattr(self._eco, "gpu_infos") and self._eco.gpu_infos) or self._eco.gpu_info:
            avg_gpu, avg_gpu_pwr = self._eco._get_avg_gpu_in_range(self._start_time, end_time)
            if avg_gpu_pwr is not None:
                gpu_energy_wh = (avg_gpu_pwr * duration) / self._eco.SECONDS_PER_HOUR
                gpu_carbon = (gpu_energy_wh / self._eco.WATTS_PER_KILOWATT) * self._eco.carbon_intensity
            else:
                valid_gpus = [g for g in self._eco.gpu_infos if isinstance(g, dict)] if hasattr(self._eco, "gpu_infos") and self._eco.gpu_infos else []
                total_tdp = sum(float(g.get("tdp", 0.0)) for g in valid_gpus) if valid_gpus else float((self._eco.gpu_info or {}).get("tdp", 100.0))
                gpu_carbon = self._eco._compute_carbon(total_tdp, avg_gpu, duration, is_gpu=True)

        total_carbon_g = cpu_carbon + gpu_carbon
        self._eco._accumulate_carbon(total_carbon_g, self.project_name, duration, avg_cpu)

        if self.save_to_file and self.output_file:
            os.makedirs(self.output_dir, exist_ok=True)
            custom_path = os.path.join(self.output_dir, self.output_file)
            try:
                exists = os.path.isfile(custom_path) and os.path.getsize(custom_path) > 0
                with open(custom_path, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    if not exists:
                        writer.writerow(["project_name", "duration_seconds", "emissions_kg", "emissions_g", "region"])
                    writer.writerow([
                        self.project_name,
                        f"{duration:.4f}",
                        f"{total_carbon_g / 1000.0:.10f}",
                        f"{total_carbon_g:.8f}",
                        self.region_code,
                    ])
            except Exception:
                pass

        self.final_emissions_g = total_carbon_g
        self.final_emissions = total_carbon_g / 1000.0
        return self.final_emissions

    def flush(self) -> None:
        pass

    def __enter__(self) -> "EmissionsTracker":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()


class OfflineEmissionsTracker(EmissionsTracker):
    def __init__(self, country_iso_code: str = "GLOBAL", **kwargs: Any) -> None:
        super().__init__(country_iso_code=country_iso_code, **kwargs)


def track_emissions(
    _func: Optional[Callable] = None,
    *,
    project_name: Optional[str] = None,
    measure_power_secs: Optional[float] = None,
    output_dir: Optional[str] = None,
    output_file: Optional[str] = None,
    country_iso_code: Optional[str] = None,
    region: Optional[str] = None,
    save_to_file: bool = True,
    **tracker_kwargs: Any,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        label = project_name or func.__name__

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                tracker = EmissionsTracker(
                    project_name=label,
                    measure_power_secs=measure_power_secs,
                    output_dir=output_dir,
                    output_file=output_file,
                    country_iso_code=country_iso_code,
                    region=region,
                    save_to_file=save_to_file,
                    **tracker_kwargs,
                )
                tracker.start()
                try:
                    return await func(*args, **kwargs)
                finally:
                    tracker.stop()

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracker = EmissionsTracker(
                project_name=label,
                measure_power_secs=measure_power_secs,
                output_dir=output_dir,
                output_file=output_file,
                country_iso_code=country_iso_code,
                region=region,
                save_to_file=save_to_file,
                **tracker_kwargs,
            )
            tracker.start()
            try:
                return func(*args, **kwargs)
            finally:
                tracker.stop()

        return sync_wrapper

    if _func is None:
        return decorator
    return decorator(_func)
