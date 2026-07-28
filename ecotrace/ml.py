from typing import Optional, List, Tuple, Dict, Any
import time
import threading
import functools
import os
import csv
import shutil
from datetime import datetime
from ecotrace.gpu import get_gpu_info, get_gpu_power_w
from .report import create_gpu_usage_chart, generate_pdf_report

class EcoTraceML:
    """Independent energy and carbon tracking engine for AI/ML models (ISO 14064 Compliant)."""
    
    def __init__(
        self,
        model_name: str = "AI Model",
        gpu_index: int = 0,
        sample_interval: float = 1.0,
        project_name: Optional[str] = None,
        epochs: Optional[int] = None,
        batch_size: Optional[int] = None,
        dataset_size: Optional[int] = None,
    ):
        self.model_name = project_name or model_name
        self.sample_interval = sample_interval
        self.epochs = epochs
        self.batch_size = batch_size
        self.dataset_size = dataset_size
        self.total_gpu_energy_joules: float = 0.0
        self.is_running: bool = False
        self._thread: Optional[threading.Thread] = None
        self.power_history: List[Tuple[float, float]] = []
        self._lock = threading.Lock()

        from ecotrace import EcoTrace
        self.eco = EcoTrace(quiet=True, check_updates=False)
        self.gpu_info: Optional[Dict[str, Any]] = self.eco.gpu_info or get_gpu_info(gpu_index, {"intel": 15.0, "amd": 75.0, "unknown": 100.0})
        self.gpu_index: Optional[int] = self.eco.gpu_index if self.eco.gpu_index is not None else gpu_index
        self._epoch_snapshots: List[Tuple[float, float]] = []  # List of per-epoch (energy_j, duration_s) snapshots

    def _carbon_intensity_gco2_per_kwh(self) -> float:
        """Normalize carbon intensity to gCO2/kWh.

        Some legacy or misconfigured intensity values can be expressed in
        kgCO2/kWh. The main EcoTrace engine uses gCO2/kWh, so we normalize
        values below 10 as kgCO2/kWh to preserve backward compatibility.
        """
        raw_intensity = getattr(self.eco, "carbon_intensity", 475.0)
        if raw_intensity <= 0.0:
            return 475.0
        return float(raw_intensity * 1000.0 if raw_intensity < 10.0 else raw_intensity)

    def _monitor_gpu(self) -> None:
        last_time = time.time()

        while self.is_running:
            time.sleep(self.sample_interval)

            current_time = time.time()
            elapsed, last_time = current_time - last_time, current_time

            current_watt = get_gpu_power_w(self.gpu_info)

            if current_watt is None:
                gpu_tdp = (self.gpu_info.get("tdp") or 100.0) if isinstance(self.gpu_info, dict) else 100.0
                current_watt = float(gpu_tdp) * 0.5

            if current_watt is not None:
                with self._lock:
                    self.total_gpu_energy_joules += current_watt * elapsed
                    self.power_history.append((current_time, current_watt))

    def snapshot_energy(self):
        """Returns a thread-safe snapshot of accumulated energy and power history.

        Useful for reading intermediate values at epoch boundaries without
        stopping the monitoring thread.

        Returns:
            tuple: ``(total_gpu_energy_joules, list_of_power_history_tuples)``
        """
        with self._lock:
            return self.total_gpu_energy_joules, list(self.power_history)

    def log_epoch(self, epoch: int, energy_j: float, duration_s: float, metrics: Optional[dict] = None):
        """Logs a per-epoch energy measurement to the CSV audit log.

        Called by ML framework callbacks to record epoch-level carbon data
        alongside the standard per-session logging.

        Args:
            epoch: Zero-based epoch index.
            energy_j: GPU energy consumed during this epoch in Joules.
            duration_s: Duration of this epoch in seconds.
            metrics: Optional dict of framework metrics (e.g. ``{'loss': 0.42}``).
        """
        gpu_kwh = energy_j / 3_600_000.0
        carbon_intensity_g = self._carbon_intensity_gco2_per_kwh()
        co2_g = (gpu_kwh * carbon_intensity_g) * 1.05  # 5 % ISO uncertainty margin
        region_str = getattr(self.eco, "region_code", "GLOBAL")
        run_id = getattr(self.eco, "_run_id", "")
        run_label = getattr(self.eco, "_run_label", "")

        label_suffix = f", loss={metrics['loss']:.4f}" if metrics and "loss" in metrics else ""
        func_name = f"ml::epoch_{epoch}::{self.model_name}{label_suffix}"

        log_file = "ecotrace_log.csv"
        file_exists = os.path.exists(log_file)
        try:
            with open(log_file, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Date", "Function", "Duration(s)", "Carbon(gCO2)",
                                     "Region", "AvgCPU(%)", "FilePath", "Line",
                                     "RunID", "RunLabel"])
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    func_name,
                    f"{duration_s:.4f}",
                    f"{co2_g:.8f}",
                    region_str,
                    "0.0",
                    "N/A",
                    "N/A",
                    run_id,
                    run_label,
                ])
        except Exception as e:
            print(f"[EcoTraceML] Could not write epoch log: {e}")
        return co2_g

    def __enter__(self):
        if self.gpu_info and self.gpu_info.get('brand') != 'Unknown':
            print(f"Starting energy tracking for {self.model_name} on GPU: {self.gpu_info['brand']} with TDP: {self.gpu_info['tdp']}W")
        else:
            print("Real data cannot be read at the moment; simulation mode is active.")

        self.total_gpu_energy_joules = 0.0
        self.power_history = []
        self.is_running = True
        self._thread = threading.Thread(target=self._monitor_gpu, daemon=True)
        self._thread.start()

        return self
    
    def __exit__(
        self,
        exc_type: Optional[type] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional[Any] = None,
    ) -> bool:
        self.is_running = False
        if self._thread:
            self._thread.join()

        # Thread-safe snapshot alignment
        with self._lock:
            total_gpu_energy_joules = self.total_gpu_energy_joules
            power_history = list(self.power_history)

        if not power_history:
            print(f"[EcoTraceML] No energy monitoring data collected for {self.model_name}.")
            return False

        gpu_kwh = total_gpu_energy_joules / 3600000.0
        carbon_intensity_g = self._carbon_intensity_gco2_per_kwh()
        co2_emitted_g_iso = (gpu_kwh * carbon_intensity_g) * 1.05

        # Update core cumulative trackers if they exist
        for attr, val in [("total_carbon", co2_emitted_g_iso), ("total_energy_kwh", gpu_kwh)]:
            if hasattr(self.eco, attr):
                setattr(self.eco, attr, getattr(self.eco, attr) + val)

        print(f"\n--- [{self.model_name}] AI Training Carbon Report (ISO 14064 Compliant) ---")
        print(f"Total Energy Consumed : {gpu_kwh:.6f} kWh ({total_gpu_energy_joules:.2f} Joules)")
        print(f"ISO 14064 CO2 Footprint: {co2_emitted_g_iso:.6f} g CO2e (Includes 5% Uncertainty Margin)\n")
        
        # Log to CSV file for report history summary
        log_file = "ecotrace_log.csv"
        file_exists = os.path.exists(log_file)
        duration = power_history[-1][0] - power_history[0][0] if len(power_history) >= 2 else 0.0
        region_str = getattr(self.eco, "region_code", "GLOBAL")
        run_id = getattr(self.eco, "_run_id", "")
        run_label = getattr(self.eco, "_run_label", "")

        try:
            with open(log_file, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Date", "Function", "Duration(s)", "Carbon(gCO2)",
                                     "Region", "AvgCPU(%)", "FilePath", "Line",
                                     "RunID", "RunLabel"])
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    f"ml::{self.model_name}",
                    f"{duration:.4f}",
                    f"{co2_emitted_g_iso:.8f}",
                    region_str,
                    "0.0",
                    "N/A",
                    "N/A",
                    run_id,
                    run_label,
                ])
        except Exception as e:
            print(f"Could not write to log CSV: {e}")

        # Scale metrics and prepare chart tracking data
        gpu_tdp = float((self.gpu_info.get("tdp") or 45.0) if isinstance(self.gpu_info, dict) else 45.0)
        gpu_utilization_samples = [(ts, min((w / gpu_tdp) * 100.0, 100.0)) for ts, w in power_history]
        report_filename = f"ecotrace_{self.model_name.lower()}_report.pdf"

        try:
            temp_chart_path = create_gpu_usage_chart(gpu_utilization_samples)
            
            if temp_chart_path and os.path.exists(temp_chart_path):
                chart_dest = f"ecotrace_{self.model_name.lower()}_chart.png"
                shutil.copy(temp_chart_path, chart_dest)
                os.remove(temp_chart_path)
                print(f"Chart image permanently saved to: {chart_dest}")

            dynamic_cpu_info = getattr(self.eco, "cpu_info", None) or {
                "brand": "Standard Processor",
                "cores": os.cpu_count() or 4,
                "tdp": 65.0
            }

            generate_pdf_report(
                filename=report_filename,
                cpu_info=dynamic_cpu_info,
                gpu_info=self.gpu_info,
                region_code=region_str,
                gpu_samples=gpu_utilization_samples,
                api_key=getattr(self.eco, "api_key", None)
            )
            print(f"PDF report successfully generated: {report_filename}")
        except Exception as e:
            print(f"Could not generate integrated PDF/Chart report: {e}")

        return False
    
def ecotrace_ml(
    model_name: str = "AI Model",
    gpu_index: int = 0,
    sample_interval: float = 1.0,
    project_name: Optional[str] = None,
    epochs: Optional[int] = None,
    batch_size: Optional[int] = None,
    dataset_size: Optional[int] = None,
):
    """
    Decorator for tracking energy and carbon emissions of AI/ML model training using EcoTraceML context manager.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with EcoTraceML(model_name=model_name, gpu_index=gpu_index, sample_interval=sample_interval,
                            project_name=project_name, epochs=epochs, batch_size=batch_size, dataset_size=dataset_size):
                return func(*args, **kwargs)
        return wrapper
    return decorator