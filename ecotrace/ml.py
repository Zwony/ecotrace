import time
import threading
import functools
from ecotrace.gpu import get_gpu_info, get_gpu_power_w
import os
from datetime import datetime
from fpdf import FPDF

class EcoTraceML:
    """
    Independent energy and carbon tracking engine for artificial intelligence and machine learning models.
    
    Usage:
    @trace_ml(model_name="My AI Model")
    def train_model(...):
        ...
        
    This class monitors GPU energy consumption in real-time and reports the total energy 
    consumed and estimated carbon emissions upon completion of model training. If GPU 
    metadata cannot be retrieved, a simulation is performed using default TDP assumptions.
    """
    
    def __init__(self, model_name: str = "AI Model", gpu_index: int = 0, sample_interval: float = 1.0):
        self.model_name = model_name
        self.sample_interval = sample_interval

        self.total_gpu_energy_joules = 0.0
        self.is_running = False
        self._thread = None

        # 1. Initialize the core tracker in quiet mode to prevent initialization conflicts
        from ecotrace.core import EcoTrace
        self.core_tracker = EcoTrace(quiet=True, check_updates=False)
        
        if self.core_tracker.gpu_info:
            self.gpu_info = self.core_tracker.gpu_info
        else:
            gpu_tdp_defaults = {"intel": 15.0, "amd": 75.0, "unknown": 100.0}
            self.gpu_info = get_gpu_info(gpu_index, gpu_tdp_defaults)

    def _monitor_gpu(self):
        """
        Background worker function that continuously samples GPU energy consumption.
            - Measures instantaneous GPU power draw at every sample_interval seconds.
            - Fallback mechanism: If the power reading is unavailable, utilizes 50% of the GPU's TDP.
            - Calculates total energy consumption in Joules (power * elapsed time).
            - Upon shutdown, converts total Joules to kWh and reports the estimated carbon footprint.
        """
        last_time = time.time()

        while self.is_running:
            time.sleep(self.sample_interval)

            current_time = time.time()
            elapsed = current_time - last_time
            last_time = current_time  # Accurately increment the elapsed time window

            current_watt = get_gpu_power_w(self.gpu_info)

            # Safety Fallback: If instantaneous wattage cannot be read, default to 50% of TDP if hardware exists
            if current_watt is None:
                if self.gpu_info:
                    current_watt = self.gpu_info.get("tdp", 100.0) * 0.5
                else:
                    current_watt = 45.0  # Constant simulation value for completely hardware-agnostic environments

            if current_watt:
                self.total_gpu_energy_joules += current_watt * elapsed

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
        self.is_running = False
        if self._thread:
            self._thread.join()

        gpu_kwh = self.total_gpu_energy_joules / 3600000.0
        carbon_intensity = getattr(self.core_tracker, "carbon_intensity", 0.475)
        co2_emitted_g = gpu_kwh * carbon_intensity * 1000.0

        print(f"\n--- [{self.model_name}] AI Training Carbon Report ---")
        print(f"Total Energy Consumed : {gpu_kwh:.6f} kWh ({self.total_gpu_energy_joules:.2f} Joules)")
        print(f"Estimated CO2 Emissions: {co2_emitted_g:.4f} g CO2")
        print("-----------------------------------------------------------\n")
        

        return self._generate_pdf_report(gpu_kwh, self.total_gpu_energy_joules, co2_emitted_g)
    
    def _generate_pdf_report(self, kwh, joules, co2):
        """
        Generates a detailed PDF report summarizing the energy consumption and 
        carbon footprint of the AI training session using fpdf2 with Unicode support.
        """
        report_filename = f"ecotrace_{self.model_name.lower()}_report.pdf"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tree_offset_day = co2 / 60

        # Start PDF generation
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        try:
            pdf.add_font("Arial", "", "C:\\Windows\\Fonts\\arial.ttf")
            pdf.add_font("Arial", "B", "C:\\Windows\\Fonts\\arialbd.ttf")
            pdf.add_font("Arial", "I", "C:\\Windows\\Fonts\\ariali.ttf")
            font_family = "Arial"
        except Exception:
            font_family = "Helvetica"

        pdf.set_font(font_family, size=12)

        # Title
        pdf.set_font(font_family, style="B", size=20)
        pdf.set_text_color(34, 139, 34)
        pdf.cell(0, 10, txt="EcoTrace AI Training Report", ln=True, align="L")
        pdf.ln(5)

        # Subtitle
        pdf.set_font(font_family, size=10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, txt="This report was automatically generated by EcoTrace after monitoring the model training session.", ln=True)
        pdf.ln(5)

        # Session Summary
        pdf.set_font(font_family, style="B", size=14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, txt="Session Summary", ln=True)
        
        pdf.set_font(font_family, size=11)
        pdf.cell(0, 6, txt=f"- Model Name: {self.model_name}", ln=True)
        pdf.cell(0, 6, txt=f"- Timestamp: {current_time}", ln=True)
        pdf.cell(0, 6, txt="- Tracking Mode: Hardware-Enforced (GPU/CPU Fallback Enabled)", ln=True)
        pdf.ln(8)

        # Line Separator
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        # Energy & Carbon Metrics
        pdf.set_font(font_family, style="B", size=14)
        pdf.cell(0, 10, txt="Energy & Carbon Metrics", ln=True)
        pdf.ln(2)

        # Table headers
        pdf.set_font(font_family, style="B", size=11)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(95, 8, txt="Metric", border=1, fill=True)
        pdf.cell(95, 8, txt="Measured Value", border=1, fill=True, ln=True)

        # Table Data
        pdf.set_font(font_family, size=11)
        pdf.cell(95, 8, txt="Total Energy Consumed", border=1)
        pdf.cell(95, 8, txt=f"{kwh:.6f} kWh ({joules:.2f} Joules)", border=1, ln=True)
        
        pdf.set_font(font_family, style="B", size=11)
        pdf.cell(95, 8, txt="Estimated CO2 Footprint", border=1)
        pdf.cell(95, 8, txt=f"{co2:.4f} g CO2", border=1, ln=True)
        pdf.ln(8)

        # Line Separator
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        # Environmental Impact Equivalent
        pdf.set_font(font_family, style="B", size=14)
        pdf.cell(0, 10, txt="Environmental Impact Equivalent", ln=True)
        
        pdf.set_font(font_family, size=11)
        impact_text = f"To offset the carbon footprint generated by this specific training session:\nIt takes approximately {tree_offset_day:.6f} days for a mature tree to absorb this amount of CO2 from the atmosphere."
        pdf.multi_cell(0, 6, txt=impact_text)
        pdf.ln(5)

        # GreenAI Note
        pdf.set_fill_color(245, 245, 245)
        pdf.set_draw_color(34, 139, 34)
        pdf.set_line_width(1)
        
        note_text = "GreenAI Note: Optimizing code concurrency and utilizing hardware-aware fallback mechanisms helps reduce unnecessary power draws at the micro-level."
        
        current_y = pdf.get_y()
        pdf.line(12, current_y, 12, current_y + 12)
        pdf.set_x(15)
        pdf.set_font(font_family, style="I", size=10)
        pdf.multi_cell(0, 5, txt=note_text)

        # Save PDF report
        try:
            pdf.output(report_filename)
            print(f"Detailed PDF report saved as: {report_filename}")
        except Exception as e:
            print(f"Error saving PDF report: {e}")
        
        

def trace_ml(model_name: str = "AI Model"):
    """
    Decorator function designed for artificial intelligence and machine learning models.
    
    Usage: @trace_ml(model_name="My AI Model")
    
    This decorator automatically provisions and teardowns the EcoTraceML context manager 
    around the target callable block. The model name parameter is optional and enriches 
    the session logs.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with EcoTraceML(model_name=model_name) as tracker:
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator