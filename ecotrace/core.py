# EcoTrace: Continuous Carbon Instrumentation Engine
# Established accuracy for scalable carbon observability.
import os
import time
import psutil
import csv
import inspect
from contextlib import contextmanager
from datetime import datetime
from .config import (load_constants, validate_region_code, resolve_carbon_intensity,
                      load_gpu_tdp_defaults, fetch_live_carbon_intensity, GRID_CACHE_TTL_S,
                      identify_user_region, DEFAULT_REGION)
import functools
import asyncio
import threading
from collections import deque
import tempfile

from .logger import logger
from .exceptions import EcoTraceConfigurationError

from .ram import get_ram_info, RAM_WATT_FACTORS
from .cpu import get_cpu_info, load_tdp_database
from .gpu import get_gpu_info
from .hardware import HardwareMonitor

# --- Energy Constants ---


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
        api_key: Optional Google Gemini API key. If not provided, it will
            check the GEMINI_API_KEY environment variable.
        grid_api_key: Optional Electricity Maps API key for real-time carbon
            intensity data. If not provided, checks the ECOTRACE_GRID_API_KEY
            environment variable. Falls back to static data if unavailable.
        check_updates: If True (default), checks PyPI for newer versions at
            startup and prompts the user interactively. Set to False in CI/CD
            or non-interactive environments.

    Raises:
        TypeError: If gpu_index is not an integer or carbon_limit is not numeric.
    """

    # --- Sampling configuration ---------------------------------------------
    FULL_UTILIZATION_PERCENT = 100.0
    MONITOR_INTERVAL_S = 0.05  # 50 ms
    SAMPLE_BUFFER_SIZE = 10000  # Increased for longer sessions (8+ mins at 50ms)
    MONITOR_JOIN_TIMEOUT_S = 1.0
    BASELINE_MEASUREMENT_MS = 100  # 100ms idle baseline measurement

    # --- Unit conversion constants ------------------------------------------
    SECONDS_PER_HOUR = 3600
    WATTS_PER_KILOWATT = 1000

    def __init__(self, region_code="GLOBAL", carbon_limit=None, gpu_index=0,
                 api_key=None, grid_api_key=None, check_updates=True, quiet=False):
        # --- Auto-Update Check (v6.0) ----------------------------------------
        # Runs FIRST so the user sees the update prompt before initialization.
        # Completely fail-safe — errors are silently swallowed.
        if check_updates:
            try:
                from .updater import check_for_updates
                from . import __version__
                check_for_updates(__version__)
            except Exception:
                pass  # Update check must never block initialization

        # --- Input validation -----------------------------------------------
        if not isinstance(gpu_index, int) or gpu_index < 0:
            logger.warning(f"Invalid gpu_index={gpu_index!r}, defaulting to 0.")
            gpu_index = 0

        if carbon_limit is not None:
            if not isinstance(carbon_limit, (int, float)) or carbon_limit <= 0:
                logger.warning(f"Invalid carbon_limit={carbon_limit!r}, disabling limit.")
                carbon_limit = None

        self.carbon_limit = carbon_limit
        self.total_carbon = 0.0
        self.gpu_index = gpu_index
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.grid_api_key = grid_api_key or os.environ.get("ECOTRACE_GRID_API_KEY")
        self.quiet = quiet

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.json_path = os.path.join(self.base_dir, "constants.json")
        self.csv_path = os.path.join(self.base_dir, "cpu_spec.csv", "boaviztapi", "data", "crowdsourcing", "cpu_specs.csv")

        # Load data sources before validating region_code
        self._constants_data = load_constants(self.json_path)
        self.tdp_db = load_tdp_database(self.csv_path)
        # --- Region Selection & Auto-Detection (v6.0) ------------------------
        # If default region "GLOBAL" is present, attempt IP-based auto-detection first.
        final_region = region_code
        if region_code == "GLOBAL":
            detected = identify_user_region()
            if detected:
                final_region = detected
                logger.debug(f"Detected region: {final_region}")
            else:
                logger.info(f"Using default region: {DEFAULT_REGION}")

        self.region_code = validate_region_code(final_region, self._constants_data)

        # --- Live Grid API Integration (v6.0) --------------------------------
        # Attempts to fetch real-time carbon intensity from Electricity Maps.
        # Falls back to static constants.json data if API is unavailable.
        self._grid_cache_timestamp = 0.0  # Epoch time of last successful fetch
        self._grid_cached_intensity = None  # Cached live value
        self._intensity_source = "static"  # Tracks data source for banner

        self.carbon_intensity = self._resolve_intensity_with_live_fallback()

        self.gpu_tdp_defaults = load_gpu_tdp_defaults(self._constants_data)
        self.cpu_info = get_cpu_info(self.tdp_db, self._constants_data)
        self.gpu_info = get_gpu_info(self.gpu_index, self.gpu_tdp_defaults)
        self.ram_info = get_ram_info()
        self.hardware = HardwareMonitor()

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
        self._cpu_monitor_ref_count = 0  # Support for nested monitoring
        self._gpu_monitor_ref_count = 0
        # --- High-Resolution Monitoring State ---
        # 50ms (0.05) is the engineering sweet spot. Higher frequency hits CPU
        # overhead; lower frequency (like 15s) misses bursty micro-code.
        self.MONITOR_INTERVAL_S = 0.05
        self._monitor_interval = self.MONITOR_INTERVAL_S
        self._current_process = psutil.Process()

        # --- Initialization Sequence (v0.7.0) -------------------------------
        if not self.quiet:
            # Metadata for emission intensity resolution
            intensity_metadata = f"{self.carbon_intensity} gCO2/kWh"
            source_label = "LIVE" if self._intensity_source == "live" else "STATIC"
            
            logger.info(f"[INFO] EcoTrace instrumentation session initialized ({source_label}).")
            logger.info("-" * 53)
            logger.info(f"Region        : {self.region_code} ({intensity_metadata})")
            logger.info(f"Hardware Logic: {self.cpu_info['brand']}")
            logger.info(f"Specifications: {self.cpu_info['cores']} Cores | {self.cpu_info['tdp']}W TDP")
            
            if self.hardware.rapl_available:
                logger.info("Energy Sensor : RAPL (Exact Hardware Mode Enabled)")
            else:
                logger.info("Energy Sensor : Boavizta Advanced Estimation")
                import platform
                if platform.system() == "Linux":
                    logger.warning("RAPL access denied! Run with 'sudo' for 0% deviation exact CPU profiling.")
                
            if self.ram_info:
                logger.info(f"Memory Config : {self.ram_info['total_gb']:.1f} GB {self.ram_info['type']}")
                
            if self.gpu_info:
                logger.info(f"GPU Accelerator: {self.gpu_info['brand']} ({self.gpu_info['tdp']}W TDP)")
            
            logger.info("-" * 53)
            logger.info("[INFO] Instrumentation sequence finalized.\n")

        # NOTE: Calculating idle baseline to subtract system noise. 
        # We don't want to attribute OS background updates to YOUR code.
        self._idle_baseline_w = self._measure_idle_baseline()

    # ========================================================================
    # Live Grid API — Intensity Resolution (v6.0)
    # ========================================================================

    def _resolve_intensity_with_live_fallback(self):
        """Resolves carbon intensity using live API data with static fallback.

        Implements a three-tier resolution strategy:
        1. **Cache Hit**: If a valid cached value exists and is within the
           GRID_CACHE_TTL_S window (1 hour), returns it immediately.
        2. **Live Fetch**: Queries the Electricity Maps API for real-time
           carbon intensity data for the configured region.
        3. **Static Fallback**: If both cache and live fetch fail, falls back
           to the static ``CARBON_INTENSITY_MAP`` from ``constants.json``.

        This method is called during ``__init__`` and can be called again
        at any time to refresh the intensity value.

        Returns:
            float: Carbon intensity in gCO2/kWh from the best available
            source (live API preferred, static data as fallback).
        """
        import time as _time

        # Tier 1: Check memory cache validity (1-hour TTL)
        now = _time.time()
        if (self._grid_cached_intensity is not None
                and (now - self._grid_cache_timestamp) < GRID_CACHE_TTL_S):
            self._intensity_source = "live"
            return self._grid_cached_intensity

        # Tier 2: Attempt live API fetch
        if self.grid_api_key:
            live_intensity = fetch_live_carbon_intensity(
                self.region_code, self.grid_api_key
            )
            if live_intensity is not None:
                # Update cache with fresh value
                self._grid_cached_intensity = live_intensity
                self._grid_cache_timestamp = now
                self._intensity_source = "live"
                logger.info(f"🌍 Live grid data: {live_intensity} gCO2/kWh")
                return live_intensity
            else:
                logger.warning("⚠️ Live grid API unavailable, using static data.")

        # Tier 3: Static fallback from constants.json
        self._intensity_source = "static"
        return resolve_carbon_intensity(self.region_code, self._constants_data)

    # ========================================================================
    # Carbon calculation helpers
    # ========================================================================

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

    def _compute_carbon(self, tdp, utilization_pct, duration_s, energy_delta_j=None, is_gpu=False):
        """Computes carbon emissions from power parameters.

        Args:
            tdp: Thermal Design Power in watts.
            utilization_pct: Average utilization as a percentage (0–100).
            duration_s: Measurement duration in seconds.
            energy_delta_j: Exact hardware energy delta in Joules (optional).
            is_gpu: Flag to differentiate GPU vs CPU workloads.

        Returns:
            float: Estimated carbon emissions in gCO2.
        """
        # CPU utilization is already properly core-normalized by _get_avg_cpu_in_range
        normalized_utilization = min(max(utilization_pct, 0.0), 100.0)
        
        # Power calculation (Exact vs Estimated)
        if energy_delta_j is not None:
            # EXACT MODE: Hardware sensors isolate process footprint via utilization scaling
            main_power_wh = (energy_delta_j / 3600.0) * (normalized_utilization / 100.0)
        else:
            # ESTIMATION MODE: Non-linear Boavizta modeling for CPU, standard linear for GPU
            if not is_gpu and tdp == self.cpu_info.get('tdp'):
                power_w = self.hardware.estimate_cpu_power_w(tdp, normalized_utilization)
            else:
                power_w = tdp * (normalized_utilization / 100.0)
            main_power_wh = power_w * duration_s / self.SECONDS_PER_HOUR
        
        # RAM energy calculation - Recursive Process Tree (RSS) for accuracy
        try:
            total_rss = self._current_process.memory_info().rss
            for child in self._current_process.children(recursive=True):
                try:
                    total_rss += child.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            ram_usage_gb = total_rss / (1024**3)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            ram_usage_gb = 0.0
            
        ram_watt_factor = RAM_WATT_FACTORS.get(self.ram_info['type'], RAM_WATT_FACTORS['DDR4'])
        ram_power_wh = (ram_watt_factor * ram_usage_gb) * duration_s / self.SECONDS_PER_HOUR
        
        # Total energy consumption
        total_power_wh = main_power_wh + ram_power_wh
        
        return (total_power_wh / self.WATTS_PER_KILOWATT) * self.carbon_intensity

    def _accumulate_carbon(self, carbon_emitted, func_name, duration, avg_cpu=None, file_path=None, line_number=None):
        """Thread-safe accumulation of carbon emissions with CSV logging.

        Args:
            carbon_emitted: Carbon value in gCO2 to add to the running total.
            func_name: Name of the measured function for the audit log.
            duration: Execution duration in seconds.
            avg_cpu: Average CPU usage percentage (optional).
            file_path: Absolute path to the source file.
            line_number: Line number where the function is defined.
        """
        with self._carbon_lock:
            self.total_carbon += carbon_emitted
            self._log_to_csv(func_name, duration, carbon_emitted, avg_cpu, file_path, line_number)

    # ========================================================================
    # Monitoring infrastructure
    # ========================================================================

    def _cpu_monitor_worker(self):
        """Background thread that continuously samples process-scoped CPU usage.

        Samples at MONITOR_INTERVAL_S intervals using ``psutil.Process``,
        storing ``(timestamp, cpu_percent)`` tuples in a thread-safe deque.
        Exits gracefully if the process is no longer accessible.
        """
        # self._current_process.cpu_percent()  # Priming is already handled in __init__ baseline
        child_cache = {}  # pid -> psutil.Process object
        next_sample_time = time.perf_counter()
        while self._cpu_monitor_active:
            try:
                # 1. Start with parent process usage
                total_usage = self._current_process.cpu_percent()
                
                # 2. Get current children
                try:
                    current_children = self._current_process.children(recursive=True)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    current_children = []
                
                # 3. Update cache and sum usage
                active_pids = set()
                for child in current_children:
                    pid = child.pid
                    active_pids.add(pid)
                    if pid not in child_cache:
                        try:
                            child.cpu_percent()
                            child_cache[pid] = child
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    else:
                        try:
                            total_usage += child_cache[pid].cpu_percent()
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            del child_cache[pid]
                
                # 4. Cleanup dead processes
                for pid in list(child_cache.keys()):
                    if pid not in active_pids:
                        del child_cache[pid]
                
                timestamp = time.perf_counter()
                with self._cpu_sample_lock:
                    self._cpu_samples.append((timestamp, total_usage))
                
                # Tight timing control: account for computation duration
                next_sample_time += self._monitor_interval
                sleep_duration = next_sample_time - time.perf_counter()
                if sleep_duration > 0:
                    time.sleep(sleep_duration)
                else:
                    # Compensation for heavy loop: don't sleep, but catch up next time
                    next_sample_time = time.perf_counter()
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
            import nvidia_ml_py as pynvml  # type: ignore
        except ImportError:
            return

        handle = self.gpu_info["handle"]
        while self._gpu_monitor_active:
            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_usage = util.gpu
                power_mw = pynvml.nvmlDeviceGetPowerUsage(handle)
                timestamp = time.perf_counter()
                with self._gpu_sample_lock:
                    self._gpu_samples.append((timestamp, gpu_usage, power_mw / 1000.0))
                time.sleep(self._monitor_interval)
            except Exception:
                break

    def _start_cpu_monitor(self):
        """Spawns the background CPU sampling thread with reference counting."""
        with self._cpu_sample_lock:
            self._cpu_monitor_ref_count += 1
            if self._cpu_monitor_ref_count == 1:
                self._cpu_monitor_active = True
                self._cpu_samples.clear()
                self._cpu_monitor_thread = threading.Thread(target=self._cpu_monitor_worker, daemon=True)
                self._cpu_monitor_thread.start()

    def _stop_cpu_monitor(self):
        """Signals the CPU sampling thread to stop only when ref count hits zero."""
        with self._cpu_sample_lock:
            if self._cpu_monitor_ref_count > 0:
                self._cpu_monitor_ref_count -= 1
            
            if self._cpu_monitor_ref_count == 0 and self._cpu_monitor_active:
                self._cpu_monitor_active = False
                if self._cpu_monitor_thread:
                    self._cpu_monitor_thread.join(timeout=self.MONITOR_JOIN_TIMEOUT_S)
                    self._cpu_monitor_thread = None

    def _start_gpu_monitor(self):
        """Spawns the background GPU sampling thread with reference counting."""
        with self._gpu_sample_lock:
            self._gpu_monitor_ref_count += 1
            if self._gpu_monitor_ref_count == 1:
                self._gpu_monitor_active = True
                self._gpu_samples.clear()
                self._gpu_monitor_thread = threading.Thread(target=self._gpu_monitor_worker, daemon=True)
                self._gpu_monitor_thread.start()

    def _stop_gpu_monitor(self):
        """Signals the GPU sampling thread to stop only when ref count hits zero."""
        with self._gpu_sample_lock:
            if self._gpu_monitor_ref_count > 0:
                self._gpu_monitor_ref_count -= 1
            
            if self._gpu_monitor_ref_count == 0 and self._gpu_monitor_active:
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
            
            # Smart Core Normalization: Divide by logical cores
            raw_avg = sum(relevant_samples) / len(relevant_samples)
            core_count = psutil.cpu_count(logical=True) or 1
            return raw_avg / core_count

    def _get_avg_gpu_in_range(self, start_time, end_time):
        """Computes mean GPU utilization and power from samples within a time window.

        Args:
            start_time: Window start as a ``time.perf_counter()`` value.
            end_time: Window end as a ``time.perf_counter()`` value.

        Returns:
            tuple: (Average GPU percentage, Average Power in Watts).
            Returns (FULL_UTILIZATION_PERCENT, None) if no samples were captured.
        """
        with self._gpu_sample_lock:
            # Check length of sample to support backward compatibility if deque still has old (ts, util) items
            relevant_samples = []
            for item in self._gpu_samples:
                if len(item) == 3:
                    ts, gpu, pwr = item
                    if start_time <= ts <= end_time:
                        relevant_samples.append((gpu, pwr))
                        
        if not relevant_samples:
            return self.FULL_UTILIZATION_PERCENT, None
            
        avg_gpu = sum(s[0] for s in relevant_samples) / len(relevant_samples)
        avg_pwr = sum(s[1] for s in relevant_samples) / len(relevant_samples)
        return avg_gpu, avg_pwr

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

    def _log_to_csv(self, func_name, duration, carbon, avg_cpu=None, file_path=None, line_number=None):
        """Appends a single measurement row to the CSV audit log.

        Creates ``ecotrace_log.csv`` with headers if it doesn't exist.

        Args:
            func_name: Name of the tracked function.
            duration: Execution time in seconds.
            carbon: Estimated carbon emissions in gCO2.
            avg_cpu: Average CPU usage percentage (optional).
            file_path: Source file path.
            line_number: Source line number.
        """
        try:
            file_exists = os.path.isfile("ecotrace_log.csv")
            with open("ecotrace_log.csv", "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Date", "Function", "Duration(s)", "Carbon(gCO2)", "Region", "AvgCPU(%)", "FilePath", "Line"])
                avg_cpu_str = f"{avg_cpu:.2f}" if avg_cpu is not None else "N/A"
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    func_name, 
                    f"{duration:.4f}", 
                    f"{carbon:.8f}", 
                    self.region_code, 
                    avg_cpu_str,
                    file_path or "N/A",
                    line_number or "N/A"
                ])
        except Exception as e:
            # We must never crash the user's application solely because logging failed.
            # Usually occurs due to file contention (locks) during high-frequency execution.
            logger.warning(f"EcoTrace CSV logging failed: {e}")

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
                logger.warning(f"No GPU detected, executing '{func.__name__}' without measurement.")
                return func(*args, **kwargs)

            # --- VS Code IDE Integration ---
            # We capture the absolute source location to enable 'Hotspot' markers.
            # This allows developers to see emissions data directly in their editor gutter.
            try:
                # Capture the original location of the tracked function
                file_path = os.path.abspath(inspect.getfile(func))
                line_number = inspect.getsourcelines(func)[1]
            except Exception:
                # Fallback: Capturing location must not interrupt the measurement lifecycle
                file_path, line_number = None, None

            start_time = time.perf_counter()
            try:
                with self.gpu_monitor():
                    result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                try:
                    duration = end_time - start_time
                    avg_gpu_util, avg_gpu_pwr = self._get_avg_gpu_in_range(start_time, end_time)
                    
                    if avg_gpu_pwr is not None:
                        # EXACT GPU MODE (NVML hardware reading)
                        gpu_energy_wh = (avg_gpu_pwr * duration) / self.SECONDS_PER_HOUR
                        carbon_emitted = (gpu_energy_wh / self.WATTS_PER_KILOWATT) * self.carbon_intensity
                    else:
                        # ESTIMATION MODE (Fallback for unsupported GPUs)
                        carbon_emitted = self._compute_carbon(self.gpu_info['tdp'], avg_gpu_util, duration, is_gpu=True)

                    self._accumulate_carbon(carbon_emitted, func.__name__, duration, file_path=file_path, line_number=line_number)
                    logger.info(f"GPU Carbon Emissions: {carbon_emitted:.8f} gCO2")
                    logger.info(f"Duration     : {duration:.4f} sec")
                    logger.info(f"GPU Usage    : {avg_gpu_util:.1f}%")
                    logger.info(f"CO2          : {carbon_emitted:.8f} gCO2")
                except Exception as e:
                    logger.error(f"GPU measurement failed for '{func.__name__}': {e}")
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
        result_data = None
        func_success = False

        try:
            energy_start = self.hardware.get_cpu_energy_j()
            with self.cpu_monitor():
                if self.gpu_info:
                    with self.gpu_monitor():
                        result_data = func(*args, **kwargs)
                else:
                    result_data = func(*args, **kwargs)
                func_success = True
        finally:
            end_time = time.perf_counter()
            energy_end = self.hardware.get_cpu_energy_j()
            duration = end_time - start_time

            try:
                avg_cpu = self._get_avg_cpu_in_range(start_time, end_time)

                with self._cpu_sample_lock:
                    measurement_samples = list(self._cpu_samples)

                # Capture location info
                try:
                    file_path = os.path.abspath(inspect.getfile(func))
                    line_number = inspect.getsourcelines(func)[1]
                except Exception:
                    file_path, line_number = None, None

                energy_delta_j = None
                if energy_start is not None and energy_end is not None:
                    energy_delta_j = max(0.0, energy_end - energy_start)

                carbon_emitted = self._compute_carbon(self.cpu_info['tdp'], avg_cpu, duration, energy_delta_j=energy_delta_j)
                self._accumulate_carbon(carbon_emitted, func.__name__, duration, avg_cpu, file_path=file_path, line_number=line_number)

                if func_success:
                    return {
                        "func_name": func.__name__,
                        "duration": duration,
                        "avg_cpu": avg_cpu,
                        "carbon": carbon_emitted,
                        "cpu_samples": measurement_samples,
                        "result": result_data
                    }
            except Exception as e:
                logger.error(f"Measurement failed for '{func.__name__}': {e}")
                if func_success:
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
        result_data = None
        func_success = False

        try:
            energy_start = self.hardware.get_cpu_energy_j()
            with self.cpu_monitor():
                try:
                    if self.gpu_info:
                        with self.gpu_monitor():
                            result_data = await func(*args, **kwargs)
                    else:
                        result_data = await func(*args, **kwargs)
                    func_success = True
                finally:
                    await asyncio.sleep(self.MONITOR_INTERVAL_S)  # Allow trailing samples to be captured
        finally:
            end_time = time.perf_counter()
            energy_end = self.hardware.get_cpu_energy_j()
            duration = end_time - start_time

            try:
                avg_cpu = self._get_avg_cpu_in_range(start_time, end_time)

                with self._cpu_sample_lock:
                    measurement_samples = list(self._cpu_samples)

                energy_delta_j = None
                if energy_start is not None and energy_end is not None:
                    energy_delta_j = max(0.0, energy_end - energy_start)

                carbon_emitted = self._compute_carbon(self.cpu_info['tdp'], avg_cpu, duration, energy_delta_j=energy_delta_j)
                self._accumulate_carbon(carbon_emitted, func.__name__, duration, avg_cpu)

                if func_success:
                    return {
                        "func_name": func.__name__,
                        "duration": duration,
                        "avg_cpu": avg_cpu,
                        "carbon": carbon_emitted,
                        "cpu_samples": measurement_samples,
                        "result": result_data
                    }
            except Exception as e:
                logger.error(f"Async measurement failed for '{func.__name__}': {e}")
                if func_success:
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
        logger.info(f"Comparison Results:")
        logger.info(f"Function 1: {result1['func_name']} - Duration: {result1['duration']:.4f} sec - CO2: {result1['carbon']:.8f} gCO2")
        logger.info(f"Function 2: {result2['func_name']} - Duration: {result2['duration']:.4f} sec - CO2: {result2['carbon']:.8f} gCO2")
        return {"func1": result1, "func2": result2}

    # ========================================================================
    # Reporting
    # ========================================================================

    def generate_pdf_report(self, filename="ecotrace_full_report.pdf", comparison=None, cpu_samples=None, gpu_samples=None):
        """Generates a comprehensive PDF audit report dynamically.
        
        If cpu_samples or gpu_samples are not provided, the engine automatically
        snapshots the internal session deques for full-history reporting.
        """
        from .report import generate_pdf_report as generate_pdf
        
        # CPU Samples snapshot
        final_cpu_samples = None
        if cpu_samples is not None:
            final_cpu_samples = list(cpu_samples)
        else:
            with self._cpu_sample_lock:
                final_cpu_samples = list(self._cpu_samples)
                
        # GPU Samples snapshot
        final_gpu_samples = None
        if gpu_samples is not None:
            final_gpu_samples = list(gpu_samples)
        elif self.gpu_info:
            with self._gpu_sample_lock:
                final_gpu_samples = list(self._gpu_samples)

        generate_pdf(
            filename=filename,
            cpu_info=self.cpu_info,
            gpu_info=self.gpu_info,
            region_code=self.region_code,
            comparison=comparison,
            cpu_samples=final_cpu_samples,
            gpu_samples=final_gpu_samples,
            api_key=self.api_key
        )

    # ========================================================================
    # JSON Export (v0.8.0)
    # ========================================================================
    # Data bridge between the core engine and external consumers (VS Code
    # extension, CI/CD pipelines, custom dashboards). Produces a structured
    # JSON file that is far easier to parse than raw CSV.

    def export_json(self, filename="ecotrace_report.json", csv_path="ecotrace_log.csv"):
        """Exports session data to a structured JSON file.

        Combines hardware metadata, measurement history from the CSV audit
        log, and aggregate statistics into a single machine-readable document.
        This output is designed for consumption by the VS Code extension
        sidebar, CI/CD carbon gates, and third-party analytics tools.

        The JSON schema contains three top-level keys:

        - ``meta``: Hardware profile, region, version, and export timestamp.
        - ``measurements``: Array of per-function measurement records from
          the CSV audit log.
        - ``summary``: Aggregate statistics (total carbon, total duration,
          measurement count, top emitters).

        Args:
            filename: Output path for the JSON file. Defaults to
                ``ecotrace_report.json`` in the current working directory.
            csv_path: Path to the CSV audit log to read measurements from.
                Defaults to ``ecotrace_log.csv``.

        Raises:
            IOError: If the output file cannot be written.

        Example::

            eco = EcoTrace(region_code="TR")

            @eco.track
            def my_function():
                pass

            my_function()
            eco.export_json("report.json")
        """
        import json as _json
        from . import __version__

        # --- Build metadata block ---
        # Captures the full hardware profile so the JSON is self-contained.
        # Consumers don't need to re-detect hardware to interpret the data.
        meta = {
            "version": __version__,
            "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "region_code": self.region_code,
            "carbon_intensity": self.carbon_intensity,
            "intensity_source": self._intensity_source,
            "cpu": {
                "brand": self.cpu_info["brand"],
                "cores": self.cpu_info["cores"],
                "tdp_w": self.cpu_info["tdp"]
            },
            "ram": None,
            "gpu": None
        }

        if self.ram_info:
            meta["ram"] = {
                "total_gb": round(self.ram_info["total_gb"], 2),
                "type": self.ram_info["type"]
            }

        if self.gpu_info:
            meta["gpu"] = {
                "brand": self.gpu_info["brand"],
                "tdp_w": self.gpu_info["tdp"],
                "type": self.gpu_info["type"]
            }

        # --- Parse CSV audit log ---
        # Read the existing measurement history. If the CSV doesn't exist yet,
        # we still export the metadata — an empty measurements array is valid.
        measurements = []
        total_carbon = 0.0
        total_duration = 0.0
        func_carbon_map = {}

        if os.path.isfile(csv_path):
            try:
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            carbon_val = float(row.get("Carbon(gCO2)", 0))
                            duration_val = float(row.get("Duration(s)", 0))
                        except (ValueError, TypeError):
                            continue

                        record = {
                            "date": row.get("Date", ""),
                            "function": row.get("Function", "unknown"),
                            "duration_s": duration_val,
                            "carbon_gco2": carbon_val,
                            "region": row.get("Region", ""),
                            "avg_cpu_pct": row.get("AvgCPU(%)", "N/A"),
                            "file_path": row.get("FilePath", "N/A"),
                            "line": row.get("Line", "N/A")
                        }
                        measurements.append(record)

                        total_carbon += carbon_val
                        total_duration += duration_val

                        # Aggregate per-function totals for the top emitters list
                        fname = record["function"]
                        if fname not in func_carbon_map:
                            func_carbon_map[fname] = 0.0
                        func_carbon_map[fname] += carbon_val

            except Exception as e:
                logger.warning(f"CSV read error, exporting metadata only: {e}")

        # --- Build summary block ---
        # Top 5 most carbon-heavy functions for quick overview
        top_emitters = sorted(func_carbon_map.items(), key=lambda x: x[1], reverse=True)[:5]

        summary = {
            "total_carbon_gco2": round(total_carbon, 8),
            "total_duration_s": round(total_duration, 4),
            "measurement_count": len(measurements),
            "session_carbon_gco2": round(self.total_carbon, 8),
            "top_emitters": [
                {"function": name, "carbon_gco2": round(carbon, 8)}
                for name, carbon in top_emitters
            ]
        }

        # --- Write JSON output ---
        report = {
            "meta": meta,
            "measurements": measurements,
            "summary": summary
        }

        with open(filename, "w", encoding="utf-8") as f:
            _json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"JSON rapor yazıldı: {filename} ({len(measurements)} kayıt)")

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
            if self.gpu_info:
                with self.gpu_monitor():
                    yield
            else:
                yield
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            try:
                # Calculate metrics
                avg_cpu = self._get_avg_cpu_in_range(start_time, end_time)
                cpu_carbon = self._compute_carbon(self.cpu_info['tdp'], avg_cpu, duration)
                
                gpu_carbon = 0.0
                if self.gpu_info:
                    avg_gpu = self._get_avg_gpu_in_range(start_time, end_time)
                    gpu_carbon = self._compute_carbon(self.gpu_info['tdp'], avg_gpu, duration)
                
                carbon_emitted = cpu_carbon + gpu_carbon
                self._accumulate_carbon(carbon_emitted, block_name, duration, avg_cpu)
                
                logger.info(f"Block '{block_name}': {duration:.3f}s, {avg_cpu:.1f}% CPU, {carbon_emitted:.6f}g CO2")
            except Exception as e:
                logger.error(f"Block measurement failed for '{block_name}': {e}")

    def __del__(self):
        """Ensures all background monitoring threads are stopped and resources released."""
        self._stop_cpu_monitor()
        self._stop_gpu_monitor()
        try:
            import nvidia_ml_py as pynvml  # type: ignore
            pynvml.nvmlShutdown()
        except (ImportError, Exception) as e:
            logger.debug(f"nvmlShutdown bypassed or failed: {e}")