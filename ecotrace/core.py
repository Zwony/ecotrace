import os
import json
import time
import psutil
import cpuinfo
import csv
from datetime import datetime
from fpdf import FPDF
import functools
import asyncio
import inspect

class EcoTrace:
    def __init__(self, region_code="TR", carbon_limit=None, gpu_index = 0):
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
        

        print("\n--- EcoTrace Initialized ---")
        print(f"Region  : {self.region_code} ({self.carbon_intensity} gCO2/kWh)")
        print(f"CPU     : {self.cpu_info['brand']}")
        print(f"Cores   : {self.cpu_info['cores']}")
        print(f"TDP     : {self.cpu_info['tdp']}W")
        if self.gpu_info:
            print(f"GPU     : {self.gpu_info['brand']}")
            print(f"GPU TDP : {self.gpu_info['tdp']}W")
        print("----------------------------\n")

    
    def generate_pdf_report(self, filename="ecotrace_full_report.pdf", comparison=None):
        """Generates a detailed PDF report with device info and all measurements."""
        try:
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
            
            # --- 1. TITLE ---
            pdf.set_font("helvetica", 'B', 20)
            pdf.set_text_color(46, 139, 87)
            pdf.cell(200, 15, txt="EcoTrace Analysis Report", ln=True, align='C')
            pdf.ln(5)

            # --- 2. SYSTEM INFO ---
            pdf.set_fill_color(245, 245, 245)
            pdf.set_font("helvetica", 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, txt=" System Information", ln=True, fill=True)
            
            pdf.set_font("helvetica", size=10)
            pdf.cell(100, 8, txt=f"CPU: {self.cpu_info['brand']}", ln=False)
            pdf.cell(100, 8, txt=f"Cores: {self.cpu_info['cores']}", ln=True)
            pdf.cell(100, 8, txt=f"TDP: {self.cpu_info['tdp']}W", ln=False)
            pdf.cell(100, 8, txt=f"Region: {self.region_code}", ln=True)
            if self.gpu_info:
                pdf.cell(100, 8, txt=f"GPU: {self.gpu_info['brand']}", ln=False)
                pdf.cell(100, 8, txt=f"GPU TDP: {self.gpu_info['tdp']}W", ln=True)
            pdf.ln(10)

            # --- 3. FUNCTION HISTORY ---
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
                pdf.cell(40, 8, row[0], border=1)
                pdf.cell(50, 8, row[1], border=1)
                pdf.cell(25, 8, row[2], border=1)
                pdf.cell(45, 8, row[3], border=1)
                pdf.cell(30, 8, row[4], border=1, ln=True)
                try: total_sum += float(row[3])
                except: pass

            # --- 4. SUMMARY ---
            pdf.ln(10)
            pdf.set_font("helvetica", 'B', 14)
            pdf.set_fill_color(46, 139, 87)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 15, txt=f"TOTAL CUMULATIVE EMISSIONS: {total_sum:.8f} gCO2", border=1, fill=True, align='C', ln=True)

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

        except Exception as e:
            print(f"\n[EcoTrace] PDF Error: {e}")

    # --- DIGER METODLAR (AYNEN KORUNDU) ---
    def _load_tdp_database(self):
        tdp_dict = {}
        if not os.path.exists(self.csv_path): return tdp_dict
        try:
            with open(self.csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    m_name = row.get('name', '').lower().strip()
                    tdp_val = row.get('tdp')
                    if m_name and tdp_val:
                        try: tdp_dict[m_name] = float(tdp_val)
                        except: continue
        except Exception: pass
        return tdp_dict

    def _get_carbon_intensity(self):
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("CARBON_INTENSITY_MAP", {}).get(self.region_code, 475)
            return 475 
        except Exception: return 475

    def _get_cpu_info(self):
        info = cpuinfo.get_cpu_info()
        brand = info.get("brand_raw", "Unknown CPU")
        clean_brand = brand.lower()
        clean_brand = clean_brand.replace("(r)", "").replace("(tm)", "")
        # "13th gen", "12th gen" gibi nesil öneklerini temizle
        import re
        clean_brand = re.sub(r'\d+th\s+gen', '', clean_brand)
        clean_brand = " ".join(clean_brand.split())  # çift boşlukları temizle

        found_tdp = 65.0

        # 1. Tam eşleşme — en güvenilir
        if clean_brand in self.tdp_db:
            found_tdp = self.tdp_db[clean_brand]
        else:
            # 2. Kısmi eşleşme — fallback
            for model_name, tdp in self.tdp_db.items():
                if model_name == clean_brand:
                    found_tdp = tdp
                    break
                if clean_brand in model_name and len(clean_brand) > 10:
                    found_tdp = tdp
                    break

        return {"brand": brand, "cores": psutil.cpu_count(logical=False), "tdp": found_tdp}
    
    def _get_gpu_info(self):
        # 1. NVIDIA — pynvml ile
        try:
            import nvidia_ml_py as pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(self.gpu_index)
            name = pynvml.nvmlDeviceGetName(handle)
            tdp = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000
            return {"brand": name, "tdp": tdp, "type": "nvidia", "handle": handle}
        except Exception:
            pass

        # 2. AMD / Intel — wmi ile (Windows)
        try:
            import wmi
            w = wmi.WMI()
            for i, gpu in enumerate(w.Win32_VideoController()):
                if i == self.gpu_index:
                    name = gpu.Name
                if "intel" in name.lower():
                    return {"brand": name, "tdp": 15.0, "type": "intel", "handle": None}
                elif "amd" in name.lower() or "radeon" in name.lower():
                    return {"brand": name, "tdp": 75.0, "type": "amd", "handle": None}
                else:
                    return {"brand": name, "tdp": 100.0, "type": "unknown", "handle": None}
        except Exception:
            pass

        return None
    
    
    def track(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            cpu_before = psutil.cpu_percent(interval=None)
            result = func(*args, **kwargs)
            cpu_after = psutil.cpu_percent(interval=None)
            end_time = time.perf_counter()
            duration = end_time - start_time
            avg_cpu_usage = (cpu_before + cpu_after) / 2
            power_usage = (self.cpu_info['tdp'] * (avg_cpu_usage / 100) * duration) / 3600
            carbon_emitted = (power_usage / 1000) * self.carbon_intensity
            self.total_carbon += carbon_emitted
            self._log_to_csv(func.__name__, duration, carbon_emitted)
            print(f"\n[EcoTrace] Function : {func.__name__}\n[EcoTrace] Duration : {duration:.4f} sec\n[EcoTrace] CO2      : {carbon_emitted:.8f} gCO2")
            return result
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)           
            async def async_wrapper(*args, **kwargs):
                psutil.cpu_percent(interval=None)
                start_time = time.perf_counter()
                result = await func(*args, **kwargs)
                end_time = time.perf_counter()
                duration = end_time - start_time
                avg_cpu = psutil.cpu_percent(interval=0.1)
                power_usage = (self.cpu_info['tdp'] * (avg_cpu / 100) * duration) / 3600
                carbon_emitted = (power_usage / 1000) * self.carbon_intensity
                self.total_carbon += carbon_emitted
                self._log_to_csv(func.__name__, duration, carbon_emitted)
                print(f"\n[EcoTrace] Function : {func.__name__}")
                print(f"[EcoTrace] Duration : {duration:.4f} sec")
                print(f"[EcoTrace] CO2      : {carbon_emitted:.8f} gCO2")
                return result
                
            return async_wrapper
        
        return wrapper

    def _log_to_csv(self, func_name, duration, carbon):
        file_exists = os.path.isfile("ecotrace_log.csv")
        with open("ecotrace_log.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Date", "Function", "Duration(s)", "Carbon(gCO2)", "Region"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), func_name, f"{duration:.4f}", f"{carbon:.8f}", self.region_code])
    
    def measure(self, func)-> dict:
        psutil.cpu_percent(interval=None)
        start_time = time.perf_counter()
        func()
        end_time = time.perf_counter()
        duration  = end_time - start_time
        avg_cpu = psutil.cpu_percent(interval=0.1)
        power_usage_wh = (self.cpu_info['tdp'] * (avg_cpu / 100) * duration) / 3600
        carbon_emitted = (power_usage_wh / 1000) * self.carbon_intensity
        return {"func_name": func.__name__, "duration": duration, "avg_cpu": avg_cpu, "carbon": carbon_emitted}
    
    def compare(self, func1, func2)-> dict:
        result1 = self.measure(func1)
        result2 = self.measure(func2)
        print(f"\n[EcoTrace] Comparison Results:")
        print(f"Function 1: {result1['func_name']} - Duration: {result1['duration']:.4f} sec - CO2: {result1['carbon']:.8f} gCO2")
        print(f"Function 2: {result2['func_name']} - Duration: {result2['duration']:.4f} sec - CO2: {result2['carbon']:.8f} gCO2")
        return {"func1": result1, "func2": result2}
    
    def track_gpu(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.gpu_info is None:
                print(f"\n[EcoTrace] No GPU found, skipping measurement.")
                return func(*args, **kwargs)
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            duration = end_time - start_time
            power_usage = (self.gpu_info['tdp'] * duration) / 3600
            carbon_emitted = (power_usage / 1000) * self.carbon_intensity
            self.total_carbon += carbon_emitted
            self._log_to_csv(func.__name__, duration, carbon_emitted)
            print(f"\n[EcoTrace] GPU Function : {func.__name__}")
            print(f"[EcoTrace] Duration     : {duration:.4f} sec")
            print(f"[EcoTrace] CO2          : {carbon_emitted:.8f} gCO2")
            return result
        return wrapper