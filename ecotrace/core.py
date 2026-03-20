import os
import json
import re
import time
import psutil
import cpuinfo
import csv
from contextlib import contextmanager
from datetime import datetime
from fpdf import FPDF
import functools
import asyncio
import inspect
import threading
from collections import deque
import matplotlib.pyplot as plt
import tempfile


class EcoTrace:
    """Tracks CPU/GPU energy consumption and estimates carbon emissions per function call.

    Carbon formula: energy (Wh) = TDP * cpu% * duration / 3600  →  gCO2 = (Wh/1000) * carbon_intensity

    Args:
        region_code: ISO country code for grid carbon intensity lookup (default: "TR").
        carbon_limit: Reserved for future budget alerts. Not enforced yet.
        gpu_index: Which GPU to monitor when multiple are present.
    """

    def __init__(self, region_code="TR", carbon_limit=None, gpu_index=0):
        self.region_code = region_code
        self.carbon_limit = carbon_limit
        self.total_carbon = 0.0
        self.gpu_index = gpu_index

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.json_path = os.path.join(self.base_dir, "constants.json")
        self.csv_path = os.path.join(self.base_dir, "cpu_spec.csv", "boaviztapi", "data", "crowdsourcing", "cpu_specs.csv")

        self.tdp_db = self._load_tdp_database()
        self.carbon_intensity = self._get_carbon_intensity()
        self.cpu_info = self._get_cpu_info()
        self.gpu_info = self._get_gpu_info()

        self._cpu_monitor_active = False
        self._cpu_monitor_thread = None
        self._cpu_samples = deque(maxlen=1000)
        self._cpu_sample_lock = threading.Lock()
        self._monitor_interval = 0.05  # 50ms sampling interval
        self._current_process = psutil.Process()

        print("\n--- EcoTrace Initialized ---")
        print(f"Region  : {self.region_code} ({self.carbon_intensity} gCO2/kWh)")
        print(f"CPU     : {self.cpu_info['brand']}")
        print(f"Cores   : {self.cpu_info['cores']}")
        print(f"TDP     : {self.cpu_info['tdp']}W")
        if self.gpu_info:
            print(f"GPU     : {self.gpu_info['brand']}")
            print(f"GPU TDP : {self.gpu_info['tdp']}W")
        print("----------------------------\n")

    def _create_cpu_usage_chart(self, samples_data):
        """Renders a CPU usage line chart from sample data and saves it to a temp PNG file."""
        if not samples_data:
            return None

        try:
            timestamps = [t for t, _ in samples_data]
            cpu_values = [c for _, c in samples_data]
            relative_times = [(t - timestamps[0]) for t in timestamps]

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(relative_times, cpu_values, linewidth=2, color='#2E8B57')
            ax.fill_between(relative_times, cpu_values, alpha=0.3, color='#2E8B57')
            ax.set_xlabel('Time (seconds)', fontsize=10)
            ax.set_ylabel('CPU Usage (%)', fontsize=10)
            ax.set_title('CPU Usage Over Time', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 100)
            plt.tight_layout()

            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return temp_file.name

        except Exception as e:
            print(f"[EcoTrace] Chart generation failed: {e}")
            return None

    def generate_pdf_report(self, filename="ecotrace_full_report.pdf", comparison=None, cpu_samples=None):
        """Generates a PDF report with system info, function history, CPU chart, and total emissions."""
        try:
            # Load logged history from CSV
            history = []
            log_file = "ecotrace_log.csv"
            if os.path.exists(log_file):
                with open(log_file, mode='r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)
                    for row in reader:
                        if len(row) >= 5:
                            history.append(row)

            pdf = FPDF()
            pdf.add_page()

            pdf.set_font("helvetica", 'B', 20)
            pdf.set_text_color(46, 139, 87)
            pdf.cell(200, 15, txt="EcoTrace Analysis Report", ln=True, align='C')
            pdf.ln(5)

            pdf.set_fill_color(245, 245, 245)
            pdf.set_font("helvetica", 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, txt=" System Information", ln=True, fill=True)
            pdf.set_font("helvetica", size=10)
            cpu_display = "".join(c for c in str(self.cpu_info['brand']) if ord(c) < 128)
            pdf.cell(100, 8, txt=f"CPU: {cpu_display}", ln=False)
            pdf.cell(100, 8, txt=f"Cores: {self.cpu_info['cores']}", ln=True)
            pdf.cell(100, 8, txt=f"TDP: {self.cpu_info['tdp']}W", ln=False)
            pdf.cell(100, 8, txt=f"Region: {self.region_code}", ln=True)
            if self.gpu_info:
                gpu_display = "".join(c for c in str(self.gpu_info['brand']) if ord(c) < 128)
                pdf.cell(100, 8, txt=f"GPU: {gpu_display}", ln=False)
                pdf.cell(100, 8, txt=f"GPU TDP: {self.gpu_info['tdp']}W", ln=True)
            pdf.ln(10)

            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(0, 10, txt=" Function History", ln=True, fill=True)
            pdf.ln(2)
            pdf.set_font("helvetica", 'B', 9)
            pdf.set_fill_color(200, 220, 200)
            pdf.cell(40, 10, "Date", border=1, fill=True)
            pdf.cell(50, 10, "Function", border=1, fill=True)
            pdf.cell(25, 10, "Duration(s)", border=1, fill=True)
            pdf.cell(45, 10, "Carbon(gCO2)", border=1, fill=True)
            pdf.cell(30, 10, "Region", border=1, fill=True, ln=True)

            pdf.set_font("helvetica", size=8)
            total_sum = 0.0
            for row in history:
                # Clean function name for PDF
                safe_func_name = "".join(c for c in str(row[1]) if ord(c) < 128)
                pdf.cell(40, 8, str(row[0]), border=1)
                pdf.cell(50, 8, safe_func_name, border=1)
                pdf.cell(25, 8, str(row[2]), border=1)
                pdf.cell(45, 8, str(row[3]), border=1)
                pdf.cell(30, 8, str(row[4]), border=1, ln=True)
                try:
                    total_sum += float(row[3])
                except:
                    pass

            # Optional CPU usage chart page
            chart_image_path = None
            try:
                if cpu_samples:
                    with self._cpu_sample_lock:
                        samples_list = list(cpu_samples)

                    if samples_list:
                        chart_image_path = self._create_cpu_usage_chart(samples_list)

                        if chart_image_path:
                            pdf.add_page()
                            pdf.set_font("helvetica", 'B', 12)
                            pdf.cell(0, 10, txt=" CPU Usage Over Time", ln=True, fill=True)
                            pdf.ln(5)
                            pdf.image(chart_image_path, x=10, y=50, w=190)
                            pdf.ln(120)

                            avg_cpu = sum(c for _, c in samples_list) / len(samples_list)
                            max_cpu = max(c for _, c in samples_list)
                            min_cpu = min(c for _, c in samples_list)

                            pdf.set_font("helvetica", size=9)
                            pdf.cell(0, 8, txt=f"Average CPU: {avg_cpu:.1f}% | Peak: {max_cpu:.1f}% | Min: {min_cpu:.1f}%", ln=True)

            except Exception as e:
                print(f"[EcoTrace] Chart section error: {e}")

            pdf.ln(10)
            pdf.set_font("helvetica", 'B', 14)
            pdf.set_fill_color(46, 139, 87)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 15, txt=f"TOTAL CUMULATIVE EMISSIONS: {total_sum:.8f} gCO2", border=1, fill=True, align='C', ln=True)

            # Optional side-by-side comparison table
            if comparison is not None:
                r1 = comparison.get("func1", {})
                r2 = comparison.get("func2", {})
                pdf.ln(10)
                pdf.set_font("helvetica", 'B', 12)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 10, txt="Comparison Analysis", ln=True, fill=True)
                pdf.set_font("helvetica", 'B', 9)
                pdf.set_fill_color(200, 220, 200)
                pdf.cell(50, 10, "Function",     border=1, fill=True)
                pdf.cell(35, 10, "Duration(s)",  border=1, fill=True)
                pdf.cell(35, 10, "Avg CPU(%)",   border=1, fill=True)
                pdf.cell(50, 10, "Carbon(gCO2)", border=1, fill=True, ln=True)
                pdf.set_font("helvetica", size=9)
                pdf.cell(50, 8, r1.get("func_name", ""), border=1)
                pdf.cell(35, 8, f"{r1.get('duration', 0):.4f}", border=1)
                pdf.cell(35, 8, f"{r1.get('avg_cpu', 0):.1f}", border=1)
                pdf.cell(50, 8, f"{r1.get('carbon', 0):.8f}", border=1, ln=True)
                pdf.cell(50, 8, r2.get("func_name", ""), border=1)
                pdf.cell(35, 8, f"{r2.get('duration', 0):.4f}", border=1)
                pdf.cell(35, 8, f"{r2.get('avg_cpu', 0):.1f}", border=1)
                pdf.cell(50, 8, f"{r2.get('carbon', 0):.8f}", border=1, ln=True)

            pdf.output(filename)
            print(f"\n[EcoTrace] Report saved: {filename}")

            # Clean up the temporary chart image
            if chart_image_path and os.path.exists(chart_image_path):
                try:
                    os.unlink(chart_image_path)
                except Exception:
                    pass

        except Exception as e:
            print(f"\n[EcoTrace] PDF Error: {e}")

    def _load_tdp_database(self):
        """Parses the CPU spec CSV into a {model_name: tdp} dict."""
        tdp_dict = {}
        if not os.path.exists(self.csv_path):
            return tdp_dict
        try:
            with open(self.csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    m_name = row.get('name', '').lower().strip()
                    tdp_val = row.get('tdp')
                    if m_name and tdp_val:
                        try:
                            tdp_dict[m_name] = float(tdp_val)
                        except:
                            continue
        except Exception:
            pass
        return tdp_dict

    def _get_carbon_intensity(self):
        """Looks up gCO2/kWh for the configured region. Falls back to 475 (IEA 2022 global avg)."""
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("CARBON_INTENSITY_MAP", {}).get(self.region_code, 475)
            return 475
        except Exception:
            return 475

    def _get_cpu_info(self):
        """Detects the current CPU and looks up its TDP. Falls back to 65W if not found in the database."""
        info = cpuinfo.get_cpu_info()
        brand = info.get("brand_raw", "Unknown CPU")
        
        # Clean brand string for matching, but keep a display version
        display_brand = "".join(c for c in brand if ord(c) < 128).replace("(R)", "").replace("(TM)", "").replace("(r)", "").replace("(tm)", "")
        
        clean_brand = brand.lower()
        clean_brand = clean_brand.replace("(r)", "").replace("(tm)", "")
        clean_brand = re.sub(r'\d+th\s+gen', '', clean_brand)
        clean_brand = " ".join(clean_brand.split())

        found_tdp = 65.0  # Common mid-range desktop TDP fallback

        if clean_brand in self.tdp_db:
            found_tdp = self.tdp_db[clean_brand]
        else:
            for model_name, tdp in self.tdp_db.items():
                if model_name == clean_brand:
                    found_tdp = tdp
                    break
                if clean_brand in model_name and len(clean_brand) > 10:
                    found_tdp = tdp
                    break

        return {"brand": display_brand, "cores": psutil.cpu_count(logical=False), "tdp": found_tdp}

    def _get_gpu_info(self):
        """Detects GPU and TDP. Tries NVIDIA (pynvml), then AMD/Intel via WMI (Windows only).
        Uses estimated TDPs when the driver can't report exact values: Intel ~15W, AMD ~75W, unknown ~100W."""

        try:
            import nvidia_ml_py as pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(self.gpu_index)
            name = pynvml.nvmlDeviceGetName(handle)
            # Clean name for PDF compatibility
            display_name = "".join(c for c in name if ord(c) < 128).replace("(R)", "").replace("(TM)", "").replace("(r)", "").replace("(tm)", "")
            tdp = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000
            return {"brand": display_name, "tdp": tdp, "type": "nvidia", "handle": handle}
        except Exception:
            pass

        try:
            import wmi
            w = wmi.WMI()
            for i, gpu in enumerate(w.Win32_VideoController()):
                if i == self.gpu_index:
                    name = gpu.Name
                    # Clean name for PDF compatibility
                    display_name = "".join(c for c in name if ord(c) < 128).replace("(R)", "").replace("(TM)", "").replace("(r)", "").replace("(tm)", "")
                    if "intel" in name.lower():
                        return {"brand": display_name, "tdp": 15.0, "type": "intel", "handle": None}
                    elif "amd" in name.lower() or "radeon" in name.lower():
                        return {"brand": display_name, "tdp": 75.0, "type": "amd", "handle": None}
                    else:
                        return {"brand": display_name, "tdp": 100.0, "type": "unknown", "handle": None}
        except Exception:
            pass

        return None

    def track(self, func):
        """Decorator for measuring carbon emissions. Handles both sync and async functions automatically.
        Uses continuous CPU sampling via measure() and measure_async() for accurate results."""

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return (await self.measure_async(func, *args, **kwargs))["result"]
            return async_wrapper

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.measure(func, *args, **kwargs)["result"]

        return wrapper

    def _log_to_csv(self, func_name, duration, carbon):
        """Appends one measurement row to ecotrace_log.csv, creating the file with headers if needed."""
        file_exists = os.path.isfile("ecotrace_log.csv")
        with open("ecotrace_log.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Date", "Function", "Duration(s)", "Carbon(gCO2)", "Region"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), func_name, f"{duration:.4f}", f"{carbon:.8f}", self.region_code])

    def _cpu_monitor_worker(self):
        """Background thread: samples process CPU usage every 50ms and stores (timestamp, cpu%) tuples."""
        self._current_process.cpu_percent()  # Discard first call — psutil always returns 0.0 initially
        while self._cpu_monitor_active:
            try:
                cpu_usage = self._current_process.cpu_percent()
                timestamp = time.perf_counter()
                with self._cpu_sample_lock:
                    self._cpu_samples.append((timestamp, cpu_usage))
                time.sleep(self._monitor_interval)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            except Exception:
                break

    def _start_cpu_monitor(self):
        """Spawns the background CPU sampling thread."""
        if not self._cpu_monitor_active:
            self._cpu_monitor_active = True
            self._cpu_samples.clear()
            self._cpu_monitor_thread = threading.Thread(target=self._cpu_monitor_worker, daemon=True)
            self._cpu_monitor_thread.start()

    def _stop_cpu_monitor(self):
        """Signals the sampling thread to stop and waits for it to exit."""
        self._cpu_monitor_active = False
        if self._cpu_monitor_thread:
            self._cpu_monitor_thread.join(timeout=1.0)
            self._cpu_monitor_thread = None

    def _get_avg_cpu_in_range(self, start_time, end_time):
        """Returns the mean CPU% from samples collected between two perf_counter timestamps."""
        with self._cpu_sample_lock:
            relevant_samples = [
                cpu for ts, cpu in self._cpu_samples
                if start_time <= ts <= end_time
            ]
            if not relevant_samples:
                return self._current_process.cpu_percent(interval=0.01)  # Fallback
            return sum(relevant_samples) / len(relevant_samples)

    @contextmanager
    def cpu_monitor(self):
        """Context manager that starts CPU monitoring on enter and stops it on exit."""
        self._start_cpu_monitor()
        try:
            yield self
        finally:
            self._stop_cpu_monitor()

    async def measure_async(self, func, *args, **kwargs):
        """Runs an async function and measures its carbon emissions using continuous CPU sampling.
        More accurate than @track for bursty or long-running async workloads.
        Returns a dict with func_name, duration, avg_cpu, carbon, cpu_samples, and the function result."""

        start_time = time.perf_counter()
        with self.cpu_monitor():
            try:
                result_data = await func(*args, **kwargs)
            except Exception as e:
                raise e
            finally:
                await asyncio.sleep(0.05)  # Allow trailing samples to be captured
                end_time = time.perf_counter()
                duration = end_time - start_time

            avg_cpu = self._get_avg_cpu_in_range(start_time, end_time)

            with self._cpu_sample_lock:
                measurement_samples = list(self._cpu_samples)

            power_usage_wh = (self.cpu_info['tdp'] * (avg_cpu / 100) * duration) / 3600  # Wh
            carbon_emitted = (power_usage_wh / 1000) * self.carbon_intensity

            self.total_carbon += carbon_emitted
            self._log_to_csv(func.__name__, duration, carbon_emitted)

            return {
                "func_name": func.__name__,
                "duration": duration,
                "avg_cpu": avg_cpu,
                "carbon": carbon_emitted,
                "cpu_samples": measurement_samples,
                "result": result_data
            }

    def measure(self, func, *args, **kwargs):
        """Measures carbon emissions of a sync function call."""
        start_time = time.perf_counter()
        with self.cpu_monitor():
            result_data = func(*args, **kwargs)
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            avg_cpu = self._get_avg_cpu_in_range(start_time, end_time)
            
            with self._cpu_sample_lock:
                measurement_samples = list(self._cpu_samples)
            
            power_usage_wh = (self.cpu_info['tdp'] * (avg_cpu / 100) * duration) / 3600
            carbon_emitted = (power_usage_wh / 1000) * self.carbon_intensity
            
            self.total_carbon += carbon_emitted
            self._log_to_csv(func.__name__, duration, carbon_emitted)
            
            return {
                "func_name": func.__name__,
                "duration": duration,
                "avg_cpu": avg_cpu,
                "carbon": carbon_emitted,
                "cpu_samples": measurement_samples,
                "result": result_data
            }

    def compare(self, func1, func2) -> dict:
        """Runs two functions and prints a side-by-side comparison of their duration and emissions."""
        result1 = self.measure(func1)
        result2 = self.measure(func2)
        print(f"\n[EcoTrace] Comparison Results:")
        print(f"Function 1: {result1['func_name']} - Duration: {result1['duration']:.4f} sec - CO2: {result1['carbon']:.8f} gCO2")
        print(f"Function 2: {result2['func_name']} - Duration: {result2['duration']:.4f} sec - CO2: {result2['carbon']:.8f} gCO2")
        return {"func1": result1, "func2": result2}

    def __del__(self):
        """Ensures the background monitoring thread is stopped on garbage collection."""
        self._stop_cpu_monitor()

    def track_gpu(self, func):
        """Decorator for estimating GPU carbon emissions. Assumes full TDP for the entire duration
        since GPU workloads typically run at or near maximum power draw."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.gpu_info is None:
                print(f"\n[EcoTrace] No GPU found, skipping measurement.")
                return func(*args, **kwargs)
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            duration = end_time - start_time
            power_usage = (self.gpu_info['tdp'] * duration) / 3600  # Wh (full TDP assumed)
            carbon_emitted = (power_usage / 1000) * self.carbon_intensity
            self.total_carbon += carbon_emitted
            self._log_to_csv(func.__name__, duration, carbon_emitted)
            print(f"\n[EcoTrace] GPU Function : {func.__name__}")
            print(f"[EcoTrace] Duration     : {duration:.4f} sec")
            print(f"[EcoTrace] CO2          : {carbon_emitted:.8f} gCO2")
            return result
        return wrapper