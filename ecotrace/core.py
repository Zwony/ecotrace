# EcoTrace: Continuous Carbon Instrumentation Engine
# Established accuracy for scalable carbon observability.
import asyncio
import atexit
import csv
import functools
import inspect
import json
import os
import sys
import threading
import time
import uuid
import warnings
import weakref
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psutil

from . import __version__
from .config import (
    DEFAULT_REGION,
    GRID_CACHE_TTL_S,
    fetch_live_carbon_intensity,
    identify_user_region,
    load_cli_config,
    load_constants,
    load_gpu_tdp_defaults,
    resolve_carbon_intensity,
    validate_region_code,
)
from .cpu import get_cpu_info, load_tdp_database
from .gpu import get_all_gpu_info, get_gpu_info
from .hardware import HardwareMonitor
from .logger import logger
from .ram import RAM_WATT_FACTORS, get_ram_info

# --- Energy Constants ---


def _atexit_session_summaries():
    for instance in list(EcoTrace._instances):
        try:
            instance._print_session_summary()
        except Exception as e:
            logger.debug(f"Atexit summary error: {e}")

atexit.register(_atexit_session_summaries)

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

    _instances = weakref.WeakSet()

    # --- Unit conversion constants ------------------------------------------
    SECONDS_PER_HOUR = 3600
    WATTS_PER_KILOWATT = 1000

    def __init__(self, region_code="GLOBAL", carbon_limit=None, gpu_index=0,
                 api_key=None, grid_api_key=None, check_updates=True, quiet=False,
                 on_budget_exceeded=None, session_summary=True, run_label=None):
        # Auto-update check
        if check_updates:
            try:
                from . import __version__
                from .updater import check_for_updates
                check_for_updates(__version__)
            except Exception as e:
                logger.debug(f"Auto-update check failed: {e}")

        # Input validation
        if not isinstance(gpu_index, int) or gpu_index < 0:
            logger.warning(f"Invalid gpu_index={gpu_index!r}, defaulting to 0.")
            gpu_index = 0

        if carbon_limit is not None:
            if not isinstance(carbon_limit, (int, float)) or carbon_limit <= 0:
                logger.warning(f"Invalid carbon_limit={carbon_limit!r}, disabling limit.")
                carbon_limit = None

        self.carbon_limit = carbon_limit
        self.total_carbon = 0.0
        self.total_energy_kwh = 0.0
        self.gpu_index = gpu_index
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.grid_api_key = grid_api_key or os.environ.get("ECOTRACE_GRID_API_KEY")
        self.quiet = quiet

        # Session run identity
        self._run_id = uuid.uuid4().hex[:12]
        self._run_label = run_label or ""

        # Carbon budget thresholds
        self._on_budget_exceeded = on_budget_exceeded
        self._budget_warning_fired = False
        self._budget_exceeded_fired = False
        self._tracked_functions_count = 0
        self._exporters = []
        self._exporter_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="EcoTrace-Exporter")

        # Cloud exporter configuration
        cli_cfg = load_cli_config()
        cloud_key = api_key if (isinstance(api_key, str) and api_key.startswith("eco_usr_")) else (
            os.environ.get("ECOTRACE_CLOUD_KEY") or cli_cfg.get("api_key")
        )
        self.cloud_key = cloud_key
        if self.cloud_key and isinstance(self.cloud_key, str) and self.cloud_key.startswith("eco_usr_"):
            try:
                from .exporters.cloud import CloudExporter
                cloud_exp = CloudExporter(api_key=self.cloud_key, endpoint=cli_cfg.get("endpoint"))
                self.add_exporter(cloud_exp)
            except Exception as e:
                logger.debug(f"Auto CloudExporter registration failed: {e}")

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.json_path = os.path.join(self.base_dir, "constants.json")
        self.csv_path = os.path.join(self.base_dir, "cpu_data.csv")

        # Load data sources before validating region_code
        self._constants_data = load_constants(self.json_path)
        self.tdp_db = load_tdp_database(self.csv_path)
        # Region selection and auto-detection
        final_region = region_code
        if region_code == "GLOBAL":
            detected = identify_user_region()
            if detected:
                final_region = detected
                logger.debug(f"Detected region: {final_region}")
            else:
                logger.info(f"Using default region: {DEFAULT_REGION}")

        self.region_code = validate_region_code(final_region, self._constants_data)

        # Real-time grid carbon intensity configuration
        self._grid_cache_timestamp = 0.0
        self._grid_cached_intensity = None
        self._intensity_source = "static"

        self.carbon_intensity = self._resolve_intensity_with_live_fallback()

        self.gpu_tdp_defaults = load_gpu_tdp_defaults(self._constants_data)
        self.cpu_info = get_cpu_info(self.tdp_db, self._constants_data)

        all_gpus = [g for g in get_all_gpu_info(self.gpu_tdp_defaults) if isinstance(g, dict)]
        if self.gpu_index > 0:
            warnings.warn(
                "gpu_index is deprecated in v1.6.0 and will be removed in a future version. "
                "Multi-GPU is now automatically tracked.",
                DeprecationWarning,
                stacklevel=2,
            )
            selected = [g for g in all_gpus if g.get("index") == self.gpu_index]
            if selected:
                self.gpu_infos: List[Dict[str, Any]] = selected
                self.gpu_info: Optional[Dict[str, Any]] = selected[0]
            else:
                single = get_gpu_info(self.gpu_index, self.gpu_tdp_defaults)
                self.gpu_infos = [single] if isinstance(single, dict) else []
                self.gpu_info = single
        else:
            self.gpu_infos = all_gpus
            self.gpu_info = all_gpus[0] if all_gpus else None

        self.gpu_count = len(self.gpu_infos)
        self.ram_info = get_ram_info()
        self.hardware = HardwareMonitor()

        # Monitoring state
        self._carbon_lock = threading.Lock()
        self._gpu_monitor_active = False
        self._gpu_monitor_thread = None
        self._gpu_samples = deque(maxlen=self.SAMPLE_BUFFER_SIZE)
        self._gpu_sample_lock = threading.Lock()
        self._cpu_monitor_active = False
        self._cpu_monitor_thread = None
        self._cpu_samples = deque(maxlen=self.SAMPLE_BUFFER_SIZE)
        self._cpu_sample_lock = threading.Lock()
        self._cpu_monitor_ref_count = 0
        self._gpu_monitor_ref_count = 0
        self._monitor_interval = self.MONITOR_INTERVAL_S
        self._current_process = psutil.Process()
        self._paused = False
        self._paused_at = None
        self._total_paused_duration = 0.0

        # Initialization banner
        if not self.quiet:
            intensity_metadata = f"{self.carbon_intensity} gCO2/kWh"
            source_label = "LIVE" if self._intensity_source == "live" else "STATIC"
            
            logger.info(f"[INFO] EcoTrace instrumentation session initialized ({source_label}).")
            logger.info("-" * 53)
            logger.info(f"Run ID        : {self._run_id}" + (f" [{self._run_label}]" if self._run_label else ""))
            logger.info(f"Region        : {self.region_code} ({intensity_metadata})")
            cpu_brand = self.cpu_info.get('brand', 'Unknown') if isinstance(self.cpu_info, dict) else 'Unknown'
            cpu_cores = self.cpu_info.get('cores', 1) if isinstance(self.cpu_info, dict) else 1
            cpu_tdp = self.cpu_info.get('tdp', 65.0) if isinstance(self.cpu_info, dict) else 65.0
            logger.info(f"Hardware Logic: {cpu_brand}")
            logger.info(f"Specifications: {cpu_cores} Cores | {cpu_tdp}W TDP")
            
            if self.hardware.rapl_available:
                logger.info("Energy Sensor : RAPL (Exact Hardware Mode Enabled)")
            elif self.hardware.apple_silicon_available:
                logger.info("Energy Sensor : Apple Silicon (powermetrics)")
            else:
                logger.info("Energy Sensor : Prediction Mode (Boavizta Advanced Estimation, ~15-20% error margin)")
                import platform
                if platform.system() == "Linux":
                    logger.warning("RAPL access denied! Run with 'sudo' for 0% deviation exact CPU profiling.")
                elif platform.system() == "Darwin":
                    logger.warning("Apple Silicon powermetrics access denied! Run with 'sudo' to allow exact energy profiling (0% deviation).")
                
            if self.ram_info and isinstance(self.ram_info, dict):
                ram_gb = self.ram_info.get('total_gb', 0.0)
                ram_type_str = self.ram_info.get('type', 'DDR4')
                logger.info(f"Memory Config : {ram_gb:.1f} GB {ram_type_str}")
                
            if hasattr(self, "gpu_infos") and self.gpu_infos:
                valid_gpus = [g for g in self.gpu_infos if isinstance(g, dict)]
                if len(valid_gpus) == 1:
                    gpu_brand_str = valid_gpus[0].get('brand', 'Unknown')
                    gpu_tdp_val = valid_gpus[0].get('tdp', 0.0)
                    logger.info(f"GPU Accelerator: {gpu_brand_str} ({gpu_tdp_val}W TDP)")
                elif len(valid_gpus) > 1:
                    total_tdp = sum(float(g.get('tdp', 0.0)) for g in valid_gpus)
                    names = ", ".join(str(g.get('brand', 'Unknown')) for g in valid_gpus)
                    logger.info(f"GPU Accelerators ({len(valid_gpus)}x): {names} ({total_tdp:.1f}W Total TDP)")
            elif self.gpu_info and isinstance(self.gpu_info, dict):
                gpu_brand_str = self.gpu_info.get('brand', 'Unknown')
                gpu_tdp_val = self.gpu_info.get('tdp', 0.0)
                logger.info(f"GPU Accelerator: {gpu_brand_str} ({gpu_tdp_val}W TDP)")
            
            logger.info("-" * 53)
            logger.info("[INFO] Instrumentation sequence finalized.\n")

        # Differential tracking idle baseline
        self._idle_baseline_pct = self._measure_idle_baseline()

        # Session lifecycle atexit summary registration
        self._session_start_time = time.perf_counter()
        self._session_summary_enabled = session_summary and not quiet
        if self._session_summary_enabled:
            EcoTrace._instances.add(self)

    # ========================================================================
    # Live Grid API — Intensity Resolution 
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
                logger.info(f" Live grid data: {live_intensity} gCO2/kWh")
                return live_intensity
            else:
                logger.warning(" Live grid API unavailable, using static data.")

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
            float: Baseline CPU utilization percentage (0-100), core-normalized.
        """
        baseline_start = time.perf_counter()
        baseline_samples = []

        # --- Ambient noise sampling ----
        # Short burst of readings before any user code runs.
        # Core-normalized so it matches _get_avg_cpu_in_range output.
        while (time.perf_counter() - baseline_start) * 1000 < self.BASELINE_MEASUREMENT_MS:
            try:
                cpu_usage = self._current_process.cpu_percent()
                baseline_samples.append(cpu_usage)
                time.sleep(self.MONITOR_INTERVAL_S)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break

        if not baseline_samples:
            return 0.0

        raw_avg = sum(baseline_samples) / len(baseline_samples)
        core_count = psutil.cpu_count(logical=True) or 1
        return raw_avg / core_count

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
            
        ram_type = 'DDR4'
        if self.ram_info and isinstance(self.ram_info, dict):
            raw_ram_type = self.ram_info.get('type')
            if raw_ram_type and isinstance(raw_ram_type, str):
                ram_type = raw_ram_type.upper()
        default_ram_watt = RAM_WATT_FACTORS.get('DDR4', 0.375)
        ram_watt_factor = RAM_WATT_FACTORS.get(ram_type, default_ram_watt)
        if ram_watt_factor is None:
            ram_watt_factor = default_ram_watt
        ram_power_wh = (ram_watt_factor * ram_usage_gb) * duration_s / self.SECONDS_PER_HOUR
        
        # Total energy consumption
        total_power_wh = main_power_wh + ram_power_wh
        
        return (total_power_wh / self.WATTS_PER_KILOWATT) * self.carbon_intensity

    def _accumulate_carbon(self, carbon_emitted, func_name, duration, avg_cpu=None, file_path=None, line_number=None):
        """Thread-safe accumulation of carbon emissions with CSV logging.

        Accumulates the emitted carbon into the session total, logs to CSV,
        and enforces carbon budget limits if configured. The library is the
        authority on budget rules — it warns and triggers callbacks here.

        Args:
            carbon_emitted: Carbon value in gCO2 to add to the running total.
            func_name: Name of the measured function for the audit log.
            duration: Execution duration in seconds.
            avg_cpu: Average CPU usage percentage (optional).
            file_path: Absolute path to the source file.
            line_number: Line number where the function is defined.
        """
        with self._carbon_lock:
            if self._paused:
                return
            self.total_carbon += carbon_emitted
            if self.carbon_intensity and self.carbon_intensity > 0:
                self.total_energy_kwh += (carbon_emitted / self.carbon_intensity)
            self._tracked_functions_count += 1
            self._log_to_csv(func_name, duration, carbon_emitted, avg_cpu, file_path, line_number)

            # --- Emit to registered telemetry exporters ----------------------
            if self._exporters:
                exporters = list(self._exporters)

                def _dispatch_exporters(exporters=exporters):
                    has_com = False
                    if sys.platform == "win32":
                        try:
                            import ctypes
                            ctypes.windll.ole32.CoInitialize(None)
                            has_com = True
                        except Exception:
                            pass
                    try:
                        for exporter in exporters:
                            try:
                                exporter.export(
                                    carbon_emitted=carbon_emitted,
                                    func_name=func_name,
                                    duration=duration,
                                    region=self.region_code,
                                    run_id=self._run_id,
                                    run_label=self._run_label
                                )
                            except Exception as e:
                                logger.debug(f"EcoTrace Exporter error: {e}")
                    finally:
                        if has_com:
                            try:
                                import ctypes
                                ctypes.windll.ole32.CoUninitialize()
                            except Exception:
                                pass

                try:
                    self._exporter_pool.submit(_dispatch_exporters)
                except Exception as e:
                    logger.debug(f"EcoTrace Exporter pool unavailable, falling back to synchronous dispatch: {e}")
                    _dispatch_exporters()

            # --- Carbon Budget Enforcement (v1.0) ----------------------------
            self._enforce_carbon_budget(func_name)

    def add_exporter(self, exporter):
        """Registers a telemetry exporter to receive carbon metrics in real-time.
        
        Args:
            exporter: An object implementing an `export(carbon_emitted, func_name, duration, region)` method.
        """
        self._exporters.append(exporter)

    def _enforce_carbon_budget(self, func_name):
        """Checks carbon budget thresholds and fires warnings/callbacks.

        Called inside _accumulate_carbon under the carbon lock. Implements a
        two-tier alert system:
            - 80% threshold: WARNING log (fires once)
            - 100% threshold: WARNING log + optional callback (fires once)

        The library is the authority on budget rules. External consumers
        (IDE, CI/CD) read the state via ``remaining_budget``.

        Args:
            func_name: Name of the function that triggered the check.
        """
        if self.carbon_limit is None:
            return

        # --- Tier 1: 80% Early Warning (fires once) -------------------------
        if not self._budget_warning_fired and self.total_carbon >= self.carbon_limit * 0.8:
            self._budget_warning_fired = True
            remaining = self.carbon_limit - self.total_carbon
            logger.warning(
                f"Carbon budget 80% consumed: {self.total_carbon:.6f} / "
                f"{self.carbon_limit:.6f} gCO2 (remaining: {remaining:.6f} gCO2)"
            )

        # --- Tier 2: Budget Exceeded (fires once + callback) -----------------
        if not self._budget_exceeded_fired and self.total_carbon >= self.carbon_limit:
            self._budget_exceeded_fired = True
            logger.warning(
                f"CARBON BUDGET EXCEEDED after '{func_name}': "
                f"{self.total_carbon:.6f} gCO2 (limit: {self.carbon_limit:.6f} gCO2)"
            )
            # --- Callback: The library notifies, the consumer decides ---------
            # on_budget_exceeded is an optional hook for custom enforcement.
            # The library fires it; the user decides what to do (log, alert, abort).
            if self._on_budget_exceeded:
                try:
                    self._on_budget_exceeded(self.total_carbon, self.carbon_limit)
                except Exception as e:
                    logger.debug(f"on_budget_exceeded callback error: {e}")

    @property
    def remaining_budget(self):
        """Returns the remaining carbon budget in gCO2, or None if no limit is set.

        This is the primary data interface for external consumers (IDE sidebar,
        CI/CD gates). The library provides the number; the consumer acts on it.

        Returns:
            float or None: Remaining gCO2 budget, or None if no limit configured.
        """
        if self.carbon_limit is None:
            return None
        return max(0.0, self.carbon_limit - self.total_carbon)

    def pause(self):
        """Temporarily pauses carbon tracking for the session."""
        with self._carbon_lock:
            if not self._paused:
                self._paused = True
                self._paused_at = time.perf_counter()
                logger.info("[EcoTrace] Instrumentation session paused.")

    def resume(self):
        """Resumes carbon tracking for the session."""
        with self._carbon_lock:
            if self._paused:
                self._paused = False
                if self._paused_at is not None:
                    self._total_paused_duration += time.perf_counter() - self._paused_at
                    self._paused_at = None
                logger.info("[EcoTrace] Instrumentation session resumed.")

    def get_summary(self) -> dict:
        """Returns the current session metrics as a structured dictionary.

        Provides programmatic access to all session data — suitable for use
        in notebooks, dashboards, custom reporting pipelines, and test assertions.
        Can be called at any point during or after a session.

        Returns:
            dict: Session summary with keys:
                - ``run_id``: Short unique ID for this session.
                - ``run_label``: Optional human-readable label.
                - ``duration_s``: Elapsed session time in seconds.
                - ``functions_tracked``: Number of tracked function calls.
                - ``total_carbon_gco2``: Cumulative carbon in gCO2.
                - ``region``: ISO region code.
                - ``carbon_intensity``: gCO2/kWh intensity value.
                - ``intensity_source``: ``'live'`` or ``'static'``.
                - ``budget``: Budget status dict (``None`` if no limit set).
                - ``equivalence``: Human-readable carbon comparison string.
                - ``hardware``: CPU/GPU/energy sensor metadata dict.
        """
        session_duration = time.perf_counter() - self._session_start_time
        current_pause = 0.0
        if self._paused and self._paused_at is not None:
            current_pause = time.perf_counter() - self._paused_at
        active_duration = max(0.0, session_duration - self._total_paused_duration - current_pause)

        # Determine energy sensor label
        if self.hardware.rapl_available:
            sensor = "RAPL (Exact Hardware)"
        elif self.hardware.apple_silicon_available:
            sensor = "Apple Silicon (powermetrics)"
        else:
            sensor = "Prediction Mode (Boavizta Estimation, ~15-20% error margin)"

        budget_info = None
        if self.carbon_limit is not None:
            remaining = self.remaining_budget
            used_pct = (self.total_carbon / self.carbon_limit * 100) if self.carbon_limit else 0.0
            budget_info = {
                "limit_gco2": self.carbon_limit,
                "remaining_gco2": remaining,
                "used_pct": round(used_pct, 2),
                "status": "EXCEEDED" if remaining == 0 else "OK",
            }

        return {
            "run_id": self._run_id,
            "run_label": self._run_label,
            "duration_s": round(active_duration, 4),
            "functions_tracked": self._tracked_functions_count,
            "total_carbon_gco2": self.total_carbon,
            "region": self.region_code,
            "carbon_intensity": self.carbon_intensity,
            "intensity_source": self._intensity_source,
            "budget": budget_info,
            "equivalence": self.equivalence(self.total_carbon),
            "hardware": {
                "cpu": self.cpu_info.get("brand", "Unknown"),
                "cores": self.cpu_info.get("cores", 0),
                "tdp_w": self.cpu_info.get("tdp", 0),
                "gpu": (
                    ", ".join(str(g.get("brand", "Unknown")) for g in self.gpu_infos if isinstance(g, dict))
                    if hasattr(self, "gpu_infos") and len(self.gpu_infos) > 1
                    else (self.gpu_info.get("brand") if isinstance(self.gpu_info, dict) else None)
                ),
                "gpu_count": self.gpu_count if hasattr(self, "gpu_count") else (1 if self.gpu_info else 0),
                "energy_sensor": sensor,
            },
        }

    def _print_session_summary(self):
        """Prints a summary table when the process exits via atexit.

        Registered in __init__ when session_summary=True and quiet=False.
        Delegates to get_summary() to avoid duplicated logic.
        """
        try:
            # Flush exporter pool before exit
            self._exporter_pool.shutdown(wait=True)

            if self._tracked_functions_count == 0:
                return  # No measurements taken, skip summary

            s = self.get_summary()

            print()
            print("=" * 55)
            print("  EcoTrace — Session Summary")
            print("=" * 55)
            print(f"  Run ID         : {s['run_id']}" + (f" [{s['run_label']}]" if s['run_label'] else ""))
            print(f"  Duration       : {s['duration_s']:.2f}s")
            print(f"  Functions      : {s['functions_tracked']} tracked")
            print(f"  Total Carbon   : {s['total_carbon_gco2']:.8f} gCO2")
            print(f"  Region         : {s['region']} ({s['carbon_intensity']} gCO2/kWh)")

            # --- Carbon Budget Status ----------------------------------------
            if s["budget"] is not None:
                b = s["budget"]
                print(f"  Budget         : {s['total_carbon_gco2']:.6f} / {b['limit_gco2']:.6f} gCO2 ({b['used_pct']:.1f}%) [{b['status']}]")

            # --- Carbon Equivalences (v1.0) ----------------------------------
            if s["equivalence"]:
                print(f"  Equivalent     : {s['equivalence']}")

            print("=" * 55)
        except Exception:
            pass  # Session summary must never crash the application

    # ========================================================================
    # Carbon Equivalences (v1.0)
    # ========================================================================
    # The library converts abstract gCO2 into human-readable comparisons.
    # Data sources: IEA 2024, EPA greenhouse gas equivalencies, published LCA.

    def equivalence(self, gco2):
        """Converts a gCO2 value into a human-readable real-world comparison.

        Uses a tiered system: selects the most relatable comparison based on
        the magnitude of the emission value. The library owns this conversion;
        external consumers (IDE, reports) can call it to enrich their display.

        Args:
            gco2: Carbon emissions in grams of CO2.

        Returns:
            str: Human-readable equivalence string, or empty string if the
            value is too small to compare meaningfully.
        """
        if gco2 <= 0:
            return ""

        # --- Equivalence factors (per 1 gCO2) --------------------------------
        # LED bulb (10W): ~5.2 gCO2/hour → 1 gCO2 ≈ 11.5 min
        # Smartphone charge: ~8.22 gCO2 per full charge
        # Car driving: ~121 gCO2/km (EU avg petrol)
        # Google search: ~0.2 gCO2 per search
        # Netflix streaming: ~36 gCO2 per hour

        if gco2 < 0.01:
            searches = gco2 / 0.2
            return f"{searches:.2f} Google searches"
        elif gco2 < 1.0:
            led_minutes = (gco2 / 5.2) * 60
            return f"{led_minutes:.1f} min of LED bulb (10W)"
        elif gco2 < 10.0:
            charges = gco2 / 8.22
            return f"{charges:.2f} smartphone charges"
        elif gco2 < 100.0:
            netflix_min = (gco2 / 36.0) * 60
            return f"{netflix_min:.1f} min of Netflix streaming"
        else:
            km = gco2 / 121.0
            return f"{km:.2f} km of car driving"

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
        
        # Initialize COM on Windows to prevent "Windows fatal exception: code 0x800401f0"
        has_com = False
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.ole32.CoInitialize(None)
                has_com = True
            except Exception:
                pass

        try:
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
        finally:
            if has_com:
                try:
                    import ctypes
                    ctypes.windll.ole32.CoUninitialize()
                except Exception:
                    pass

    def _gpu_monitor_worker(self):
        """Background thread that continuously samples GPU utilization.

        Samples at MONITOR_INTERVAL_S intervals across all active NVIDIA GPUs,
        storing ``(timestamp, avg_gpu_percent, total_power_w)`` tuples in a thread-safe deque.
        """
        gpu_list = self.gpu_infos if hasattr(self, "gpu_infos") and self.gpu_infos else ([self.gpu_info] if self.gpu_info else [])
        nvidia_gpus = [g for g in gpu_list if g and g.get("type") == "nvidia" and g.get("handle") is not None]
        if not nvidia_gpus:
            return

        import importlib
        try:
            pynvml = importlib.import_module("nvidia_ml_py")
        except ImportError:
            try:
                pynvml = importlib.import_module("pynvml")
            except ImportError:
                return

        while self._gpu_monitor_active:
            try:
                total_power_w = 0.0
                total_util = 0.0
                valid_count = 0
                for g in nvidia_gpus:
                    handle = g["handle"]
                    try:
                        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        total_util += util.gpu
                        power_mw = pynvml.nvmlDeviceGetPowerUsage(handle)
                        total_power_w += power_mw / 1000.0
                        valid_count += 1
                    except Exception as e:
                        logger.debug(f"GPU device sampling failed: {e}")
                        continue

                if valid_count > 0:
                    avg_gpu_usage = total_util / valid_count
                    timestamp = time.perf_counter()
                    with self._gpu_sample_lock:
                        self._gpu_samples.append((timestamp, avg_gpu_usage, total_power_w))
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

        Applies idle baseline subtraction so the returned value represents
        only the incremental CPU load caused by the measured code, not
        background OS activity.

        Args:
            start_time: Window start as a ``time.perf_counter()`` value.
            end_time: Window end as a ``time.perf_counter()`` value.

        Returns:
            float: Average CPU percentage (baseline-subtracted), or
            FULL_UTILIZATION_PERCENT if no samples were captured.
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
            normalized = raw_avg / core_count

            # --- Differential Tracking (v1.0) --------------------------------
            # Subtract the idle baseline measured at init time.
            # Floor at 0 to avoid negative utilization from measurement jitter.
            return max(0.0, normalized - self._idle_baseline_pct)

    def _get_source_location(self, func):
        """Returns the source file path and line number for a callable.

        Works for wrapped, decorated, and async functions by unwrapping the
        original implementation before querying inspect.
        """
        try:
            target = inspect.unwrap(func)
            file_path = os.path.abspath(inspect.getfile(target))
            line_number = inspect.getsourcelines(target)[1]
            return file_path, line_number
        except Exception:
            return None, None

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
                elif len(item) == 2:
                    ts, gpu = item
                    if start_time <= ts <= end_time:
                        relevant_samples.append((gpu, None))
                        
        if not relevant_samples:
            return self.FULL_UTILIZATION_PERCENT, None
            
        avg_gpu = sum(s[0] for s in relevant_samples) / len(relevant_samples)
        pwr_samples = [s[1] for s in relevant_samples if s[1] is not None]
        avg_pwr = sum(pwr_samples) / len(pwr_samples) if pwr_samples else None
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
            file_exists = os.path.isfile("ecotrace_log.csv") and os.path.getsize("ecotrace_log.csv") > 0
            with open("ecotrace_log.csv", "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    # v1.3.0: RunID and RunLabel appended at the end so old
                    # CSVs without these columns remain parseable (DictReader
                    # will simply return 'N/A' for missing columns).
                    writer.writerow(["Date", "Function", "Duration(s)", "Carbon(gCO2)",
                                     "Region", "AvgCPU(%)", "FilePath", "Line",
                                     "RunID", "RunLabel"])
                avg_cpu_str = f"{avg_cpu:.2f}" if avg_cpu is not None else "N/A"
                writer.writerow([
                    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    func_name,
                    f"{duration:.4f}",
                    f"{carbon:.8f}",
                    self.region_code,
                    avg_cpu_str,
                    file_path or "N/A",
                    line_number or "N/A",
                    self._run_id,
                    self._run_label,
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
                res = await self.measure_async(func, *args, **kwargs)
                return res["result"] if isinstance(res, dict) else res
            return async_wrapper

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = self.measure(func, *args, **kwargs)
            return res["result"] if isinstance(res, dict) else res

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
            if not getattr(self, "gpu_infos", None) and self.gpu_info is None:
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
                with self.cpu_monitor(), self.gpu_monitor():
                    result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                try:
                    duration = end_time - start_time
                    avg_cpu = self._get_avg_cpu_in_range(start_time, end_time)
                    cpu_carbon = self._compute_carbon(self.cpu_info['tdp'], avg_cpu, duration)
                    
                    avg_gpu_util, avg_gpu_pwr = self._get_avg_gpu_in_range(start_time, end_time)
                    if avg_gpu_pwr is not None:
                        gpu_energy_wh = (avg_gpu_pwr * duration) / self.SECONDS_PER_HOUR
                        gpu_carbon = (gpu_energy_wh / self.WATTS_PER_KILOWATT) * self.carbon_intensity
                    else:
                        valid_gpus = [g for g in self.gpu_infos if isinstance(g, dict)] if getattr(self, "gpu_infos", None) else []
                        total_tdp = sum(float(g.get('tdp', 0.0)) for g in valid_gpus) if valid_gpus else (float((self.gpu_info or {}).get('tdp', 100.0)))
                        gpu_carbon = self._compute_carbon(total_tdp, avg_gpu_util, duration, is_gpu=True)

                    carbon_emitted = cpu_carbon + gpu_carbon
                    self._accumulate_carbon(carbon_emitted, func.__name__, duration, avg_cpu=avg_cpu, file_path=file_path, line_number=line_number)
                    logger.info(f"GPU/CPU Carbon Emissions: {carbon_emitted:.8f} gCO2")
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
        energy_start = None

        try:
            energy_start = self.hardware.get_cpu_energy_j()
            with self.cpu_monitor():
                if (hasattr(self, "gpu_infos") and self.gpu_infos) or self.gpu_info:
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

            # Capture location info robustly for decorated and async functions
            file_path, line_number = self._get_source_location(func)

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
        energy_start = None

        try:
            energy_start = self.hardware.get_cpu_energy_j()
            with self.cpu_monitor():
                try:
                    if (hasattr(self, "gpu_infos") and self.gpu_infos) or self.gpu_info:
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

            # Capture location info robustly for decorated and async functions
            file_path, line_number = self._get_source_location(func)

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
        if isinstance(result1, dict) and isinstance(result2, dict):
            logger.info("Comparison Results:")
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
                
        # GPU Samples snapshot — normalize 3-tuples (ts, util, power) to
        # 2-tuples (ts, util) expected by report chart functions.
        final_gpu_samples = None
        if gpu_samples is not None:
            final_gpu_samples = [(item[0], item[1]) for item in gpu_samples]
        elif self.gpu_info:
            with self._gpu_sample_lock:
                final_gpu_samples = [(item[0], item[1]) for item in self._gpu_samples]

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
        # --- Build metadata block ---
        # Captures the full hardware profile so the JSON is self-contained.
        # Consumers don't need to re-detect hardware to interpret the data.
        ram_dict = None
        if self.ram_info and isinstance(self.ram_info, dict):
            ram_total_gb = self.ram_info.get("total_gb")
            ram_type_val = self.ram_info.get("type")
            ram_dict = {
                "total_gb": round(float(ram_total_gb if ram_total_gb is not None else 0.0), 2),
                "type": str(ram_type_val if ram_type_val is not None else "DDR4")
            }

        gpu_dict = None
        if hasattr(self, "gpu_infos") and self.gpu_infos:
            valid_gpus = [g for g in self.gpu_infos if isinstance(g, dict)]
            if valid_gpus:
                gpu_brand = ", ".join(str(g.get("brand", "Unknown")) for g in valid_gpus) if len(valid_gpus) > 1 else valid_gpus[0].get("brand")
                total_tdp = sum(float(g.get("tdp", 0.0)) for g in valid_gpus)
                gpu_type = valid_gpus[0].get("type")
                gpu_dict = {
                    "brand": str(gpu_brand if gpu_brand is not None else "Unknown"),
                    "tdp_w": float(total_tdp),
                    "type": str(gpu_type if gpu_type is not None else "Unknown"),
                    "gpu_count": len(valid_gpus),
                }
        elif self.gpu_info and isinstance(self.gpu_info, dict):
            gpu_brand = self.gpu_info.get("brand")
            gpu_tdp = self.gpu_info.get("tdp")
            gpu_type = self.gpu_info.get("type")
            gpu_dict = {
                "brand": str(gpu_brand if gpu_brand is not None else "Unknown"),
                "tdp_w": float(gpu_tdp if gpu_tdp is not None else 0.0),
                "type": str(gpu_type if gpu_type is not None else "Unknown"),
                "gpu_count": 1,
            }

        cpu_dict = {}
        if self.cpu_info and isinstance(self.cpu_info, dict):
            cpu_brand = self.cpu_info.get("brand")
            cpu_cores = self.cpu_info.get("cores")
            cpu_tdp = self.cpu_info.get("tdp")
            cpu_dict = {
                "brand": str(cpu_brand if cpu_brand is not None else "Unknown"),
                "cores": int(cpu_cores if cpu_cores is not None else 1),
                "tdp_w": float(cpu_tdp if cpu_tdp is not None else 65.0)
            }
        else:
            cpu_dict = {
                "brand": "Unknown",
                "cores": 1,
                "tdp_w": 65.0
            }

        meta = {
            "version": __version__,
            "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "run_id": self._run_id,
            "run_label": self._run_label,
            "region_code": self.region_code,
            "carbon_intensity": self.carbon_intensity,
            "intensity_source": self._intensity_source,
            "cpu": cpu_dict,
            "ram": ram_dict,
            "gpu": gpu_dict
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
                            "line": row.get("Line", "N/A"),
                            "run_id": row.get("RunID", "N/A"),
                            "run_label": row.get("RunLabel", ""),
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
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"JSON report written: {filename} ({len(measurements)} records)")

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
        try:
            with self.cpu_monitor():
                if (hasattr(self, "gpu_infos") and self.gpu_infos) or self.gpu_info:
                    with self.gpu_monitor():
                        yield
                else:
                    yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            try:
                # Calculate metrics
                avg_cpu = self._get_avg_cpu_in_range(start_time, end_time)
                cpu_carbon = self._compute_carbon(self.cpu_info['tdp'], avg_cpu, duration)
                
                gpu_carbon = 0.0
                if (hasattr(self, "gpu_infos") and self.gpu_infos) or self.gpu_info:
                    avg_gpu, avg_gpu_pwr = self._get_avg_gpu_in_range(start_time, end_time)
                    if avg_gpu_pwr is not None:
                        # EXACT GPU MODE
                        gpu_energy_wh = (avg_gpu_pwr * duration) / self.SECONDS_PER_HOUR
                        gpu_carbon = (gpu_energy_wh / self.WATTS_PER_KILOWATT) * self.carbon_intensity
                    else:
                        # ESTIMATION MODE
                        valid_gpus = [g for g in self.gpu_infos if isinstance(g, dict)] if hasattr(self, "gpu_infos") and self.gpu_infos else []
                        total_tdp = sum(float(g.get('tdp', 0.0)) for g in valid_gpus) if valid_gpus else (float((self.gpu_info or {}).get('tdp', 100.0)))
                        gpu_carbon = self._compute_carbon(total_tdp, avg_gpu, duration, is_gpu=True)
                
                carbon_emitted = cpu_carbon + gpu_carbon
                self._accumulate_carbon(carbon_emitted, block_name, duration, avg_cpu)
                
                logger.info(f"Block '{block_name}': {duration:.3f}s, {avg_cpu:.1f}% CPU, {carbon_emitted:.8f}g CO2")
            except Exception as e:
                logger.error(f"Block measurement failed for '{block_name}': {e}")

    def __del__(self):
        """Ensures all background monitoring threads are stopped and resources released."""
        try:
            self._stop_cpu_monitor()
            self._stop_gpu_monitor()
        except Exception as e:
            logger.debug(f"Cleanup error in __del__: {e}")