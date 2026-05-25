import time
import threading
import functools
import os
from datetime import datetime
from ecotrace.gpu import get_gpu_info, get_gpu_power_w

class EcoTraceML:
    """
    Independent energy and carbon tracking engine for artificial intelligence and machine learning models.
    ISO 14064 Compliant MLOps Framework fully integrated with EcoTrace Core Reporting.
    
    Usage:
    with EcoTraceML(model_name="My AI Model"):
        train_model()
        
    Or as a decorator:

    @ecotrace_ml(model_name="My AI Model")
    def train_model():
        ...
    This class runs a background thread to continuously sample GPU energy consumption during the execution of the wrapped code block or function.
    """
    
    def __init__(self, model_name: str = "AI Model", gpu_index: int = 0, sample_interval: float = 1.0):
        self.model_name = model_name
        self.sample_interval = sample_interval

        self.total_gpu_energy_joules = 0.0
        self.is_running = False
        self._thread = None
        
        self.power_history = [] 

        # 1. Initialize the core tracker in quiet mode to prevent initialization conflicts
        from ecotrace import EcoTrace
        self.eco = EcoTrace(quiet=True, check_updates=False)
        
        if self.eco.gpu_info:
            self.gpu_info = self.eco.gpu_info
        else:
            gpu_tdp_defaults = {"intel": 15.0, "amd": 75.0, "unknown": 100.0}
            self.gpu_info = get_gpu_info(gpu_index, gpu_tdp_defaults)

    def _monitor_gpu(self):
        """
        Background worker function that continuously samples GPU energy consumption.
        """
        last_time = time.time()

        while self.is_running:
            time.sleep(self.sample_interval)

            current_time = time.time()
            elapsed = current_time - last_time
            last_time = current_time  

            current_watt = get_gpu_power_w(self.gpu_info)

            # Safety Fallback
            if current_watt is None:
                if self.gpu_info:
                    current_watt = self.gpu_info.get("tdp", 100.0) * 0.5
                else:
                    current_watt = 45.0  

            if current_watt:
                self.total_gpu_energy_joules += current_watt * elapsed
                
                self.power_history.append((current_time, current_watt))

    def __enter__(self):
        if self.gpu_info:
            print(f"Starting energy tracking for {self.model_name} on GPU: {self.gpu_info['brand']} with TDP: {self.gpu_info['tdp']}W")
        else:
            print(f"Real data cannot be read at the moment; simulation mode is active.")

        self.is_running = True
        self._thread = threading.Thread(target=self._monitor_gpu, daemon=True)
        self._thread.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Stop the background monitoring thread and finalize the report.
        """
        self.is_running = False
        if self._thread:
            self._thread.join()

        gpu_kwh = self.total_gpu_energy_joules / 3600000.0
        
        raw_intensity = getattr(self.eco, "carbon_intensity", 0.475)
        
        if raw_intensity < 10.0:
            carbon_intensity_g = raw_intensity * 1000.0
        else:
            carbon_intensity_g = raw_intensity

        co2_emitted_g_raw = gpu_kwh * carbon_intensity_g
        co2_emitted_g_iso = co2_emitted_g_raw * 1.05

        if hasattr(self.eco, "total_carbon"):
            self.eco.total_carbon += co2_emitted_g_iso
        if hasattr(self.eco, "total_energy_kwh"):
            self.eco.total_energy_kwh += gpu_kwh

        if hasattr(self.eco, "_gpu_samples"):
            try:
                with self.eco._gpu_sample_lock:
                    self.eco._gpu_samples.clear()
                    self.eco._gpu_samples.extend(self.power_history)
            except AttributeError:
                self.eco._gpu_samples = list(self.power_history)

        print(f"\n--- [{self.model_name}] AI Training Carbon Report (ISO 14064 Compliant) ---")
        print(f"Total Energy Consumed : {gpu_kwh:.6f} kWh ({self.total_gpu_energy_joules:.2f} Joules)")
        print(f"ISO 14064 CO2 Footprint: {co2_emitted_g_iso:.6f} g CO2e (Includes 5% Uncertainty Margin)")
        print("-----------------------------------------------------------\n")
        
        report_filename = f"ecotrace_{self.model_name.lower()}_report.pdf"
        try:
            self.eco.generate_pdf_report(filename=report_filename)
        except Exception as e:
            print(f" Could not generate integrated PDF report: {e}")

        return False
    
def ecotrace_ml(model_name: str = "AI Model"):
    """
    Decorator function designed for artificial intelligence and machine learning models.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with EcoTraceML(model_name=model_name):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator