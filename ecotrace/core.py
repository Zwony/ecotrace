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

# --- Energy Constants ---
# RAM power consumption factors by type (Watts per GB)
RAM_WATT_FACTORS = {
    'DDR4': 0.375,  # DDR4 average power consumption per GB
    'DDR5': 0.285   # DDR5 is more efficient (lower power per GB)
}


class EcoTrace:
    """High-precision carbon tracking engine for production Python.

    Monitors CPU and GPU energy consumption at function-level granularity using
    continuous 50 ms sampling, TDP-based energy estimation, and region-specific
    carbon intensity factors.

    Energy formula:
        energy (Wh) = TDP × (utilization% / 100) × duration / 3600
        gCO2 = (Wh / 1000) × carbon_intensity

    Args:
        region_code: ISO 3166-1 alpha-2 country code for grid carbon intensity
            lookup. Falls back to DEFAULT_REGION if the code is not recognized.
        carbon_limit: Optional carbon budget threshold in gCO2. Reserved for
            future budget alert functionality.
        gpu_index: Zero-based index selecting which GPU to monitor when multiple
            devices are present. Validated to be a non-negative integer.

    Raises:
        TypeError: If gpu_index is not an integer or carbon_limit is not numeric.
    """

    # --- Estimation defaults ------------------------------------------------
    DEFAULT_CPU_TDP_W = 65.0
    DEFAULT_GPU_TDP_INTEL_W = 15.0
    DEFAULT_GPU_TDP_AMD_W = 75.0
    DEFAULT_GPU_TDP_UNKNOWN_W = 100.0
    DEFAULT_CARBON_INTENSITY = 475  # IEA 2022 global average (gCO2/kWh)
    DEFAULT_REGION = "TR"

    # --- Sampling configuration ---------------------------------------------
    FULL_UTILIZATION_PERCENT = 100.0
    MONITOR_INTERVAL_S = 0.05  # 50 ms
    SAMPLE_BUFFER_SIZE = 1000
    MONITOR_JOIN_TIMEOUT_S = 1.0
    BASELINE_MEASUREMENT_MS = 100  # 100ms idle baseline measurement

    # --- Unit conversion constants ------------------------------------------
    SECONDS_PER_HOUR = 3600
    WATTS_PER_KILOWATT = 1000

    def __init__(self, region_code="TR", carbon_limit=None, gpu_index=0):
        # --- Input validation -----------------------------------------------
        if not isinstance(gpu_index, int) or gpu_index < 0:
            print(f"[EcoTrace] WARNING: Invalid gpu_index={gpu_index!r}, defaulting to 0.")
            gpu_index = 0

        if carbon_limit is not None:
            if not isinstance(carbon_limit, (int, float)) or carbon_limit <= 0:
                print(f"[EcoTrace] WARNING: Invalid carbon_limit={carbon_limit!r}, disabling limit.")
                carbon_limit = None

        self.carbon_limit = carbon_limit
        self.total_carbon = 0.0
        self.gpu_index = gpu_index

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.json_path = os.path.join(self.base_dir, "constants.json")
        self.csv_path = os.path.join(self.base_dir, "cpu_spec.csv", "boaviztapi", "data", "crowdsourcing", "cpu_specs.csv")

        # Load data sources before validating region_code
        self.tdp_db = self._load_tdp_database()
        self._constants_data = self._load_constants()
        self.region_code = self._validate_region_code(region_code)
        self.carbon_intensity = self._resolve_carbon_intensity()
        self.gpu_tdp_defaults = self._load_gpu_tdp_defaults()
        self.cpu_info = self._get_cpu_info()
        self.gpu_info = self._get_gpu_info()
        self.ram_info = self._get_ram_info()

        # --- Monitoring state -----------------------------------------------
        self._carbon_lock = threading.Lock()
        self._gpu_monitor_active = False
        self._gpu_monitor_thread = None
        self._gpu_samples = deque(maxlen=self.SAMPLE_BUFFER_SIZE)
        self._gpu_sample_lock = threading.Lock()
        self._gpu_monitor_samples = []
        self._cpu_monitor_active = False
        self._cpu_monitor_thread = None
        self._cpu_samples = deque(maxlen=self.SAMPLE_BUFFER_SIZE)
        self._cpu_sample_lock = threading.Lock()
        self._monitor_interval = self.MONITOR_INTERVAL_S
        self._current_process = psutil.Process()

        print("\n--- EcoTrace Initialized ---")
        print(f"Region  : {self.region_code} ({self.carbon_intensity} gCO2/kWh)")
        print(f"CPU     : {self.cpu_info['brand']}")
        print(f"Cores   : {self.cpu_info['cores']}")
        print(f"TDP     : {self.cpu_info['tdp']}W")
        print(f"RAM     : {self.ram_info['total_gb']:.1f} GB {self.ram_info['type']} @ {self.ram_info['speed_mhz']}MHz")
        if self.gpu_info:
            print(f"GPU     : {self.gpu_info['brand']}")
            print(f"GPU TDP : {self.gpu_info['tdp']}W")
        print("----------------------------\n")

    # ========================================================================
    # Input validation helpers
    # ========================================================================

    def _load_constants(self):
        """Loads the full constants.json file into memory.

        Returns:
            dict: Parsed JSON contents, or empty dict on failure.
        """
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _validate_region_code(self, region_code):
        """Validates the region code against known carbon intensity entries.

        Args:
            region_code: User-provided ISO country code string.

        Returns:
            str: The validated region code, or DEFAULT_REGION if invalid.
        """
        if not isinstance(region_code, str) or not region_code.strip():
            print(f"[EcoTrace] WARNING: Invalid region_code={region_code!r}, defaulting to '{self.DEFAULT_REGION}'.")
            return self.DEFAULT_REGION

        code = region_code.strip().upper()
        intensity_map = self._constants_data.get("CARBON_INTENSITY_MAP", {})

        if code not in intensity_map:
            print(f"[EcoTrace] WARNING: Unknown region '{code}', defaulting to '{self.DEFAULT_REGION}'.")
            return self.DEFAULT_REGION
        return code

    def _resolve_carbon_intensity(self):
        """Resolves the gCO2/kWh value for the validated region code.

        Returns:
            float: Carbon intensity factor for the configured region.
        """
        return (
            self._constants_data
            .get("CARBON_INTENSITY_MAP", {})
            .get(self.region_code, self.DEFAULT_CARBON_INTENSITY)
        )

    def _load_gpu_tdp_defaults(self):
        """Loads GPU TDP default estimates from constants.json.

        Returns:
            dict: Mapping of vendor key to estimated TDP in watts.
        """
        return self._constants_data.get("GPU_TDP_DEFAULTS", {
            "intel": self.DEFAULT_GPU_TDP_INTEL_W,
            "amd": self.DEFAULT_GPU_TDP_AMD_W,
            "unknown": self.DEFAULT_GPU_TDP_UNKNOWN_W,
        })

    # ========================================================================
    # Hardware detection
    # ========================================================================

    @classmethod
    @functools.lru_cache(maxsize=1)
    def fetch_raw_cpu_info(cls):
        """Retrieves raw CPU information via py-cpuinfo.

        Results are cached globally since hardware doesn't change at runtime.

        Returns:
            dict: Raw CPU info dictionary from ``cpuinfo.get_cpu_info()``.
        """
        return cpuinfo.get_cpu_info()

    def _load_tdp_database(self):
        """Parses the Boavizta CPU spec CSV into a TDP lookup dictionary.

        Returns:
            dict: Mapping of ``{lowercase_model_name: tdp_watts}``.
        """
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
                        except ValueError:
                            continue
        except Exception:
            pass
        return tdp_dict

    def _get_cpu_info(self):
        """Detects CPU hardware and resolves TDP using a multi-source lookup chain.

        Detection order:
            1. Apple Silicon (M1/M2/M3) — fixed 25W TDP for laptop-class chips
            2. Intel/AMD — CSV database lookup with fuzzy matching
            3. Fallback to 65W (common mid-range desktop TDP)

        Returns:
            dict: CPU metadata containing brand, core count, and TDP in watts.
        """
        info = cpuinfo.get_cpu_info()
        brand = info.get("brand_raw", "Unknown CPU")
        
        # Clean brand string for matching, but keep a display version
        display_brand = "".join(c for c in brand if ord(c) < 128).replace("(R)", "").replace("(TM)", "").replace("(r)", "").replace("(tm)", "")
        
        clean_brand = brand.lower()
        clean_brand = clean_brand.replace("(r)", "").replace("(tm)", "")
        clean_brand = re.sub(r'\d+th\s+gen', '', clean_brand)
        clean_brand = " ".join(clean_brand.split())

        # Apple Silicon M-series detection
        if "apple" in clean_brand:
            found_tdp = 25.0  # M-series laptop-class average TDP
        else:
            # Intel/AMD CSV database lookup
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

        return {"brand": display_brand, "cores": psutil.cpu_count(logical=True), "tdp": found_tdp}

    def _get_ram_info(self):
        """Detects RAM specifications including type, speed, and total capacity.

        Detection order:
            1. Windows: Uses WMIC to get RAM speed in MHz
            2. Linux: Uses dmidecode to get RAM speed in MHz  
            3. Fallback: Uses psutil for total capacity only

        RAM type classification:
            - DDR5: Speed >= 4800 MHz
            - DDR4: Speed < 4800 MHz (default fallback)

        Returns:
            dict: RAM metadata containing total_gb, type, and speed_mhz.
        """
        import subprocess
        
        # Get total RAM from psutil (cross-platform)
        total_ram_gb = psutil.virtual_memory().total / (1024**3)
        
        # Initialize with fallback values
        ram_type = 'DDR4'  # Default fallback
        ram_speed = 'Unknown'
        
        try:
            if os.name == 'nt':  # Windows
                # Use WMIC to get RAM speed
                result = subprocess.run(
                    ['wmic', 'memorychip', 'get', 'speed', '/value'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Speed=' in line:
                            speed_str = line.split('=')[1].strip()
                            if speed_str and speed_str.isdigit():
                                speed_mhz = int(speed_str)
                                ram_speed = str(speed_mhz)
                                # Classify RAM type based on speed
                                ram_type = 'DDR5' if speed_mhz >= 4800 else 'DDR4'
                                break
            else:  # Linux
                # Try dmidecode for detailed RAM info
                result = subprocess.run(
                    ['sudo', 'dmidecode', '-t', 'memory'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Speed:' in line and 'MHz' in line:
                            speed_str = line.split(':')[1].strip().replace('MHz', '').strip()
                            if speed_str and speed_str.isdigit():
                                speed_mhz = int(speed_str)
                                ram_speed = str(speed_mhz)
                                ram_type = 'DDR5' if speed_mhz >= 4800 else 'DDR4'
                                break
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, PermissionError, FileNotFoundError):
            # Fallback to default values if any error occurs
            pass
        
        return {
            'total_gb': total_ram_gb,
            'type': ram_type,
            'speed_mhz': ram_speed
        }

    def _get_gpu_info(self):
        """Detects GPU hardware and resolves TDP using a tri-vendor fallback chain.

        Detection order:
            1. NVIDIA via ``pynvml`` — driver-reported power management limit
            2. AMD/Intel via WMI (Windows only) — vendor-class TDP estimates
            3. Returns ``None`` if no GPU is detected (graceful degradation)

        Returns:
            dict or None: Keys ``brand``, ``tdp``, ``type``, ``handle`` if
            a GPU is found; ``None`` otherwise.
        """
        try:
            import nvidia_ml_py as pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(self.gpu_index)
            name = pynvml.nvmlDeviceGetName(handle)
            display_name = "".join(c for c in name if ord(c) < 128).replace("(R)", "").replace("(TM)", "").replace("(r)", "").replace("(tm)", "")
            tdp = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / self.WATTS_PER_KILOWATT
            return {"brand": display_name, "tdp": tdp, "type": "nvidia", "handle": handle}
        except Exception:
            pass

        try:
            import wmi
            w = wmi.WMI()
            for i, gpu in enumerate(w.Win32_VideoController()):
                if i == self.gpu_index:
                    name = gpu.Name
                    display_name = "".join(c for c in name if ord(c) < 128).replace("(R)", "").replace("(TM)", "").replace("(r)", "").replace("(tm)", "")
                    if "intel" in name.lower():
                        return {"brand": display_name, "tdp": self.gpu_tdp_defaults.get("intel", self.DEFAULT_GPU_TDP_INTEL_W), "type": "intel", "handle": None}
                    elif "amd" in name.lower() or "radeon" in name.lower():
                        return {"brand": display_name, "tdp": self.gpu_tdp_defaults.get("amd", self.DEFAULT_GPU_TDP_AMD_W), "type": "amd", "handle": None}
                    else:
                        return {"brand": display_name, "tdp": self.gpu_tdp_defaults.get("unknown", self.DEFAULT_GPU_TDP_UNKNOWN_W), "type": "unknown", "handle": None}
        except Exception:
            pass

        return None

    # ========================================================================
    # Carbon calculation helpers
    # ========================================================================

    @staticmethod
    def _sanitize_for_pdf(text):
        """Strips non-ASCII characters for safe PDF rendering.

        Args:
            text: Input string potentially containing non-ASCII characters.

        Returns:
            str: ASCII-safe string.
        """
        return "".join(c for c in str(text) if ord(c) < 128)

    def _measure_idle_baseline(self):
        """Captures short baseline measurement for differential carbon tracking.
        
        Takes a 100ms snapshot of current system utilization to establish the
        idle baseline. This baseline is subtracted from function measurements
        to report only the code's incremental energy cost.
        
        Returns:
            float: Baseline CPU utilization percentage (0-100).
        """
        baseline_start = time.perf_counter()
        baseline_samples = []
        
        # Collect samples for baseline duration
        while (time.perf_counter() - baseline_start) * 1000 < self.BASELINE_MEASUREMENT_MS:
            try:
                cpu_usage = self._current_process.cpu_percent()
                baseline_samples.append(cpu_usage)
                time.sleep(self.MONITOR_INTERVAL_S)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
        
        return sum(baseline_samples) / len(baseline_samples) if baseline_samples else 0.0

    def _compute_carbon(self, tdp, utilization_pct, duration_s):
        """Computes carbon emissions from power parameters.

        Args:
            tdp: Thermal Design Power in watts.
            utilization_pct: Average utilization as a percentage (0–100).
            duration_s: Measurement duration in seconds.

        Returns:
            float: Estimated carbon emissions in gCO2.
        """
        # Use raw CPU utilization (psutil already provides normalized percentage)
        normalized_utilization = min(max(utilization_pct, 0.0), 100.0)
        
        # CPU energy calculation
        cpu_power_wh = (tdp * normalized_utilization / 100) * duration_s / self.SECONDS_PER_HOUR
        
        # RAM energy calculation with dynamic factor based on RAM type
        ram_usage_gb = psutil.virtual_memory().used / (1024**3)  # Convert bytes to GB
        ram_watt_factor = RAM_WATT_FACTORS.get(self.ram_info['type'], RAM_WATT_FACTORS['DDR4'])  # Fallback to DDR4
        ram_power_wh = (ram_watt_factor * ram_usage_gb) * duration_s / self.SECONDS_PER_HOUR
        
        # Total energy consumption
        total_power_wh = cpu_power_wh + ram_power_wh
        
        return (total_power_wh / self.WATTS_PER_KILOWATT) * self.carbon_intensity

    def _accumulate_carbon(self, carbon_emitted, func_name, duration, avg_cpu=None):
        """Thread-safe accumulation of carbon emissions with CSV logging.

        Args:
            carbon_emitted: Carbon value in gCO2 to add to the running total.
            func_name: Name of the measured function for the audit log.
            duration: Execution duration in seconds.
            avg_cpu: Average CPU usage percentage (optional).
        """
        with self._carbon_lock:
            self.total_carbon += carbon_emitted
            self._log_to_csv(func_name, duration, carbon_emitted, avg_cpu)

    # ========================================================================
    # Monitoring infrastructure
    # ========================================================================

    def _cpu_monitor_worker(self):
        """Background thread that continuously samples process-scoped CPU usage.

        Samples at MONITOR_INTERVAL_S intervals using ``psutil.Process``,
        storing ``(timestamp, cpu_percent)`` tuples in a thread-safe deque.
        Exits gracefully if the process is no longer accessible.
        """
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

    def _gpu_monitor_worker(self):
        """Background thread that continuously samples GPU utilization.

        Only active for NVIDIA GPUs with a valid device handle. Samples at
        MONITOR_INTERVAL_S intervals, storing ``(timestamp, gpu_percent)``
        tuples in a thread-safe deque.
        """
        if not self.gpu_info or self.gpu_info.get("handle") is None:
            return

        try:
            import nvidia_ml_py as pynvml
        except ImportError:
            return

        handle = self.gpu_info["handle"]
        while self._gpu_monitor_active:
            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_usage = util.gpu
                timestamp = time.perf_counter()
                with self._gpu_sample_lock:
                    self._gpu_samples.append((timestamp, gpu_usage))
                time.sleep(self._monitor_interval)
            except Exception:
                break

    def _start_cpu_monitor(self):
        """Spawns the background CPU sampling thread if not already running."""
        if not self._cpu_monitor_active:
            self._cpu_monitor_active = True
            self._cpu_samples.clear()
            self._cpu_monitor_thread = threading.Thread(target=self._cpu_monitor_worker, daemon=True)
            self._cpu_monitor_thread.start()

    def _stop_cpu_monitor(self):
        """Signals the CPU sampling thread to stop and waits for it to exit."""
        self._cpu_monitor_active = False
        if self._cpu_monitor_thread:
            self._cpu_monitor_thread.join(timeout=self.MONITOR_JOIN_TIMEOUT_S)
            self._cpu_monitor_thread = None

    def _start_gpu_monitor(self):
        """Spawns the background GPU sampling thread if not already running."""
        if not self._gpu_monitor_active:
            self._gpu_monitor_active = True
            self._gpu_samples.clear()
            self._gpu_monitor_thread = threading.Thread(target=self._gpu_monitor_worker, daemon=True)
            self._gpu_monitor_thread.start()

    def _stop_gpu_monitor(self):
        """Signals the GPU sampling thread to stop and waits for it to exit."""
        self._gpu_monitor_active = False
        if self._gpu_monitor_thread:
            self._gpu_monitor_thread.join(timeout=self.MONITOR_JOIN_TIMEOUT_S)
            self._gpu_monitor_thread = None

    def _get_avg_cpu_in_range(self, start_time, end_time):
        """Computes mean CPU utilization from samples within a time window.

        Args:
            start_time: Window start as a ``time.perf_counter()`` value.
            end_time: Window end as a ``time.perf_counter()`` value.

        Returns:
            float: Average CPU percentage, or FULL_UTILIZATION_PERCENT if no
            samples were captured (conservative fallback).
        """
        with self._cpu_sample_lock:
            relevant_samples = [
                cpu for ts, cpu in self._cpu_samples
                if start_time <= ts <= end_time
            ]
            if not relevant_samples:
                return self.FULL_UTILIZATION_PERCENT
            
            # Use raw CPU percentage (psutil already provides 0-100% average)
            raw_avg = sum(relevant_samples) / len(relevant_samples)
            return raw_avg

    def _get_avg_gpu_in_range(self, start_time, end_time):
        """Computes mean GPU utilization from samples within a time window.

        Args:
            start_time: Window start as a ``time.perf_counter()`` value.
            end_time: Window end as a ``time.perf_counter()`` value.

        Returns:
            float: Average GPU percentage, or FULL_UTILIZATION_PERCENT if no
            samples were captured (conservative fallback).
        """
        with self._gpu_sample_lock:
            relevant_samples = [
                gpu for ts, gpu in self._gpu_samples
                if start_time <= ts <= end_time
            ]
        if not relevant_samples:
            return self.FULL_UTILIZATION_PERCENT
        return sum(relevant_samples) / len(relevant_samples)

    @contextmanager
    def cpu_monitor(self):
        """Context manager that brackets a code block with CPU monitoring.

        Yields:
            EcoTrace: The current instance for optional chaining.
        """
        self._start_cpu_monitor()
        try:
            yield self
        finally:
            self._stop_cpu_monitor()

    @contextmanager
    def gpu_monitor(self):
        """Context manager that brackets a code block with GPU monitoring.

        Yields:
            EcoTrace: The current instance for optional chaining.
        """
        self._start_gpu_monitor()
        try:
            yield self
        finally:
            self._stop_gpu_monitor()

    # ========================================================================
    # Logging
    # ========================================================================

    def _log_to_csv(self, func_name, duration, carbon, avg_cpu=None):
        """Appends a single measurement row to the CSV audit log.

        Creates ``ecotrace_log.csv`` with headers if it doesn't exist.

        Args:
            func_name: Name of the tracked function.
            duration: Execution time in seconds.
            carbon: Estimated carbon emissions in gCO2.
            avg_cpu: Average CPU usage percentage (optional).
        """
        try:
            file_exists = os.path.isfile("ecotrace_log.csv")
            with open("ecotrace_log.csv", "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Date", "Function", "Duration(s)", "Carbon(gCO2)", "Region", "AvgCPU(%)"])
                avg_cpu_str = f"{avg_cpu:.2f}" if avg_cpu is not None else "N/A"
                writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), func_name, f"{duration:.4f}", f"{carbon:.8f}", self.region_code, avg_cpu_str])
        except Exception as e:
            print(f"[EcoTrace] WARNING: CSV logging failed: {e}")

    # ========================================================================
    # Public measurement API
    # ========================================================================

    def track(self, func):
        """Decorator that measures carbon emissions for any function call.

        Automatically detects whether the target is synchronous or asynchronous
        and selects the appropriate measurement strategy.

        Args:
            func: The function to decorate. Can be sync or async.

        Returns:
            Callable: Wrapped function that measures emissions transparently.
        """
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return (await self.measure_async(func, *args, **kwargs))["result"]
            return async_wrapper

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.measure(func, *args, **kwargs)["result"]

        return wrapper

    def track_gpu(self, func):
        """Decorator that measures GPU carbon emissions with real utilization monitoring.

        If no GPU is detected, the wrapped function executes normally without
        measurement. If the GPU becomes unavailable mid-calculation, the function
        result is preserved and a warning is logged.

        Args:
            func: The function to decorate.

        Returns:
            Callable: Wrapped function with GPU carbon measurement.
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.gpu_info is None:
                print(f"\n[EcoTrace] WARNING: No GPU detected, executing '{func.__name__}' without measurement.")
                return func(*args, **kwargs)

            start_time = time.perf_counter()
            with self.gpu_monitor():
                result = func(*args, **kwargs)
            end_time = time.perf_counter()

            try:
                duration = end_time - start_time
                avg_gpu_util = self._get_avg_gpu_in_range(start_time, end_time)
                carbon_emitted = self._compute_carbon(self.gpu_info['tdp'], avg_gpu_util, duration)

                self._accumulate_carbon(carbon_emitted, func.__name__, duration)
                print(f"\n[EcoTrace] GPU Carbon Emissions: {carbon_emitted:.8f} gCO2")
                print(f"[EcoTrace] Duration     : {duration:.4f} sec")
                print(f"[EcoTrace] GPU Usage    : {avg_gpu_util:.1f}%")
                print(f"[EcoTrace] CO2          : {carbon_emitted:.8f} gCO2")
            except Exception as e:
                print(f"[EcoTrace] WARNING: GPU measurement failed for '{func.__name__}': {e}")

            return result
        return wrapper

    def measure(self, func, *args, **kwargs):
        """Executes a synchronous function and measures its CPU carbon emissions.

        Uses continuous background sampling for accurate utilization measurement.
        If the measurement calculation fails, the function result is still returned.

        Args:
            func: Synchronous callable to measure.
            *args: Positional arguments forwarded to ``func``.
            **kwargs: Keyword arguments forwarded to ``func``.

        Returns:
            dict: Keys ``func_name``, ``duration``, ``avg_cpu``, ``carbon``,
            ``cpu_samples``, and ``result``.
        """
        start_time = time.perf_counter()
        with self.cpu_monitor():
            result_data = func(*args, **kwargs)
            end_time = time.perf_counter()
            duration = end_time - start_time

        try:
            avg_cpu = self._get_avg_cpu_in_range(start_time, end_time)

            with self._cpu_sample_lock:
                measurement_samples = list(self._cpu_samples)

            carbon_emitted = self._compute_carbon(self.cpu_info['tdp'], avg_cpu, duration)
            self._accumulate_carbon(carbon_emitted, func.__name__, duration, avg_cpu)

            return {
                "func_name": func.__name__,
                "duration": duration,
                "avg_cpu": avg_cpu,
                "carbon": carbon_emitted,
                "cpu_samples": measurement_samples,
                "result": result_data
            }
        except Exception as e:
            print(f"[EcoTrace] WARNING: Measurement failed for '{func.__name__}': {e}")
            return {
                "func_name": func.__name__,
                "duration": duration,
                "avg_cpu": 0.0,
                "carbon": 0.0,
                "cpu_samples": [],
                "result": result_data
            }

    async def measure_async(self, func, *args, **kwargs):
        """Executes an async function and measures its CPU carbon emissions.

        Uses continuous background sampling, which is particularly important
        for bursty or I/O-bound async workloads where point-in-time readings
        misrepresent actual utilization.

        Args:
            func: Async callable to measure.
            *args: Positional arguments forwarded to ``func``.
            **kwargs: Keyword arguments forwarded to ``func``.

        Returns:
            dict: Keys ``func_name``, ``duration``, ``avg_cpu``, ``carbon``,
            ``cpu_samples``, and ``result``.

        Raises:
            Exception: Re-raises any exception from the wrapped function after
            completing the measurement teardown.
        """
        start_time = time.perf_counter()
        with self.cpu_monitor():
            try:
                result_data = await func(*args, **kwargs)
            except Exception as e:
                raise e
            finally:
                await asyncio.sleep(self.MONITOR_INTERVAL_S)  # Allow trailing samples to be captured
                end_time = time.perf_counter()
                duration = end_time - start_time

        try:
            avg_cpu = self._get_avg_cpu_in_range(start_time, end_time)

            with self._cpu_sample_lock:
                measurement_samples = list(self._cpu_samples)

            carbon_emitted = self._compute_carbon(self.cpu_info['tdp'], avg_cpu, duration)
            self._accumulate_carbon(carbon_emitted, func.__name__, duration, avg_cpu)

            return {
                "func_name": func.__name__,
                "duration": duration,
                "avg_cpu": avg_cpu,
                "carbon": carbon_emitted,
                "cpu_samples": measurement_samples,
                "result": result_data
            }
        except Exception as e:
            print(f"[EcoTrace] WARNING: Async measurement failed for '{func.__name__}': {e}")
            return {
                "func_name": func.__name__,
                "duration": duration,
                "avg_cpu": 0.0,
                "carbon": 0.0,
                "cpu_samples": [],
                "result": result_data
            }

    def compare(self, func1, func2):
        """Runs two functions sequentially and compares their carbon footprints.

        Args:
            func1: First callable to measure.
            func2: Second callable to measure.

        Returns:
            dict: Keys ``func1`` and ``func2``, each containing the full
            measurement dict from ``measure()``.
        """
        result1 = self.measure(func1)
        result2 = self.measure(func2)
        print(f"\n[EcoTrace] Comparison Results:")
        print(f"Function 1: {result1['func_name']} - Duration: {result1['duration']:.4f} sec - CO2: {result1['carbon']:.8f} gCO2")
        print(f"Function 2: {result2['func_name']} - Duration: {result2['duration']:.4f} sec - CO2: {result2['carbon']:.8f} gCO2")
        return {"func1": result1, "func2": result2}

    # ========================================================================
    # Reporting
    # ========================================================================

    def _create_cpu_usage_chart(self, samples_data):
        """Renders a CPU usage line chart and saves it to a temporary PNG file.

        Args:
            samples_data: List of ``(timestamp, cpu_percent)`` tuples.

        Returns:
            str or None: Path to the generated PNG, or None on failure.
        """
        if not samples_data:
            return None

        try:
            timestamps = [t for t, _ in samples_data]
            core_count = self.cpu_info.get('cores', 1)  # Safe fallback
            cpu_values = [min(s, 100.0) for _, s in samples_data]  # Raw values with 100% cap
            relative_times = [(t - timestamps[0]) for t in timestamps]

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(relative_times, cpu_values, linewidth=2, color='#2E8B57')
            ax.fill_between(relative_times, cpu_values, alpha=0.3, color='#2E8B57')
            ax.set_xlabel('Time (seconds)', fontsize=10)
            ax.set_ylabel('Normalized CPU Usage (%)', fontsize=10)
            ax.set_title('CPU Usage Over Time (Core-Normalized)', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 110)  # Allow 10% headroom for spikes
            plt.tight_layout()

            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return temp_file.name

        except Exception as e:
            print(f"[EcoTrace] Chart generation failed: {e}")
            return None

    def generate_pdf_report(self, filename="ecotrace_full_report.pdf", comparison=None, cpu_samples=None):
        """Generates a comprehensive PDF audit report.

        Includes system hardware profile, timestamped function history,
        optional CPU usage charts, comparison analysis, and cumulative
        emission totals.

        Args:
            filename: Output PDF file path.
            comparison: Optional comparison dict from ``compare()``.
            cpu_samples: Optional list of ``(timestamp, cpu_percent)`` tuples
                for the CPU usage chart page.
        """
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

            pdf.set_font("helvetica", 'B', 20)
            pdf.set_text_color(46, 139, 87)
            pdf.cell(200, 15, txt="EcoTrace Analysis Report", ln=True, align='C')
            pdf.ln(5)

            pdf.set_fill_color(245, 245, 245)
            pdf.set_font("helvetica", 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, txt=" System Information", ln=True, fill=True)
            pdf.set_font("helvetica", size=10)
            cpu_display = self._sanitize_for_pdf(self.cpu_info['brand'])
            pdf.cell(100, 8, txt=f"CPU: {cpu_display}", ln=False)
            pdf.cell(100, 8, txt=f"Cores: {self.cpu_info['cores']}", ln=True)
            pdf.cell(100, 8, txt=f"TDP: {self.cpu_info['tdp']}W", ln=False)
            pdf.cell(100, 8, txt=f"Region: {self.region_code}", ln=True)
            if self.gpu_info:
                gpu_display = self._sanitize_for_pdf(self.gpu_info['brand'])
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
                safe_func_name = self._sanitize_for_pdf(row[1])
                pdf.cell(40, 8, str(row[0]), border=1)
                pdf.cell(50, 8, safe_func_name, border=1)
                pdf.cell(25, 8, str(row[2]), border=1)
                pdf.cell(45, 8, str(row[3]), border=1)
                pdf.cell(30, 8, str(row[4]), border=1, ln=True)
                try:
                    total_sum += float(row[3])
                except ValueError:
                    pass

            chart_image_path = None
            try:
                if cpu_samples:
                    with self._cpu_sample_lock:
                        samples_list = list(cpu_samples)

                    if samples_list:
                        # Use raw CPU values with 100% cap
                        normalized_samples = [
                            (t, min(s, 100.0)) 
                            for t, s in samples_list
                        ]
                        chart_image_path = self._create_cpu_usage_chart(normalized_samples)

                        if chart_image_path:
                            pdf.add_page()
                            pdf.set_font("helvetica", 'B', 12)
                            pdf.cell(0, 10, txt=" CPU Usage Over Time (Core-Normalized)", ln=True, fill=True)
                            pdf.ln(5)
                            pdf.image(chart_image_path, x=10, y=50, w=190)
                            pdf.ln(120)

                            # Calculate stats from normalized values
                            normalized_values = [s for _, s in normalized_samples]
                            avg_cpu = sum(normalized_values) / len(normalized_values)
                            max_cpu = max(normalized_values)
                            min_cpu = min(normalized_values)

                            pdf.set_font("helvetica", size=9)
                            pdf.cell(0, 8, txt=f"Average CPU: {avg_cpu:.1f}% | Peak: {max_cpu:.1f}% | Min: {min_cpu:.1f}%", ln=True)

            except Exception as e:
                print(f"[EcoTrace] Chart section error: {e}")

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

            # Performance Insights Section
            if history:
                pdf.ln(15)
                pdf.set_font("helvetica", 'B', 12)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 10, txt="Performance Insights", ln=True, fill=True)
                pdf.set_font("helvetica", 'B', 9)
                pdf.set_fill_color(240, 240, 200)
                pdf.cell(60, 10, "Function", border=1, fill=True)
                pdf.cell(40, 10, "Avg CPU", border=1, fill=True)
                pdf.cell(40, 10, "Duration", border=1, fill=True)
                pdf.cell(50, 10, "Recommendation", border=1, fill=True, ln=True)
                pdf.set_font("helvetica", size=8)
                
                for row in history[-5:]:  # Last 5 functions
                    if len(row) >= 4:
                        func_name = row[1][:15] + "..." if len(row[1]) > 15 else row[1]
                        duration = float(row[2])
                        
                        # Generate insights based on performance metrics
                        insights = []
                        if duration > 5.0:
                            insights.append("Long execution: Check I/O bottlenecks")
                        elif duration > 2.0:
                            insights.append("Consider async implementation")
                        
                        # CPU-based insights (use stored avg_cpu from CSV if available)
                        if len(row) > 4:  # If avg_cpu is stored in CSV
                            estimated_cpu = min(float(row[4]), 100.0)
                        else:  # Fallback estimation from carbon data
                            estimated_cpu = min((float(row[3]) / 0.0005) * 100, 100.0)
                        if estimated_cpu > 70:
                            insights.append("High CPU: Optimize loops")
                        elif estimated_cpu < 20:
                            insights.append("Low CPU: Consider batching")
                        
                        if not insights:
                            insights.append("Performance looks optimal")
                        
                        pdf.cell(60, 8, func_name, border=1)
                        pdf.cell(40, 8, f"{estimated_cpu:.1f}%", border=1)
                        pdf.cell(40, 8, f"{duration:.2f}s", border=1)
                        pdf.cell(50, 8, insights[0][:20] + "..." if len(insights[0]) > 20 else insights[0], border=1, ln=True)

            pdf.output(filename)
            print(f"\n[EcoTrace] Report saved: {filename}")

            if chart_image_path and os.path.exists(chart_image_path):
                try:
                    os.unlink(chart_image_path)
                except Exception:
                    pass

        except Exception as e:
            print(f"\n[EcoTrace] PDF Error: {e}")

    # ========================================================================
    # Lifecycle
    # ========================================================================

    @contextmanager
    def track_block(self, block_name="custom_block"):
        """Context manager for tracking arbitrary code blocks.

        Usage:
            with eco.track_block("data_processing"):
                # Your code here
                result = expensive_operation()
        
        Args:
            block_name: Name to use for the tracked block in reports.

        Yields:
            None: Control flow continues within the context.
        """
        start_time = time.perf_counter()
        with self.cpu_monitor():
            try:
                yield
            finally:
                end_time = time.perf_counter()
                duration = end_time - start_time
                
                # Calculate metrics
                avg_cpu = self._get_avg_cpu_in_range(start_time, end_time)
                carbon_emitted = self._compute_carbon(self.cpu_info['tdp'], avg_cpu, duration)
                self._accumulate_carbon(carbon_emitted, block_name, duration, avg_cpu)
                
                print(f"[EcoTrace] Block '{block_name}': {duration:.3f}s, {avg_cpu:.1f}% CPU, {carbon_emitted:.6f}g CO2")

    def __del__(self):
        """Ensures all background monitoring threads are stopped on cleanup."""
        self._stop_cpu_monitor()
        self._stop_gpu_monitor()