import os
import platform
import subprocess
import plistlib
from .logger import logger

class HardwareMonitor:
    """Hardware-level energy monitoring using exact RAPL sensors or advanced estimation.

    Implements a hybrid approach to zero-configuration carbon tracking:
    1. Hardware Mode (RAPL): Reads raw energy counters on supported hardware (Linux).
    2. Advanced Estimation Mode: Falls back to Boavizta's logarithmic load curve
       to eliminate linear TDP estimation errors on unsupported systems.
    """

    def __init__(self):
        self.system = platform.system()
        self.rapl_available = self._check_rapl()
        self.apple_silicon_available = self._check_apple_silicon()

    def _check_rapl(self):
        """Checks for Intel/AMD RAPL (Running Average Power Limit) access."""
        if self.system != "Linux":
            return False
        
        rapl_path = "/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj"
        if os.path.exists(rapl_path):
            try:
                with open(rapl_path, "r") as f:
                    f.read()
                return True
            except (PermissionError, IOError):
                # Fail silently to preserve the zero-config experience.
                logger.debug("RAPL found but permission denied.")
                return False
        return False

    def _check_apple_silicon(self):
        """Detects Apple Silicon (M-series) with accessible powermetrics.

        Uses ``sudo -n powermetrics`` (non-interactive) to probe access.
        Falls back gracefully to Boavizta estimation if unavailable.

        Returns:
            bool: True if powermetrics is readable without a password prompt.
        """
        if self.system != "Darwin" or platform.machine() != "arm64":
            return False
        try:
            result = subprocess.run(
                ["sudo", "-n", "powermetrics", "--samplers", "cpu_power",
                 "-n", "1", "-i", "1", "--format", "plist"],
                capture_output=True,
                timeout=3,
            )
            # Exit code 0 means we got data; non-zero means permission denied
            if result.returncode == 0 and result.stdout:
                plistlib.loads(result.stdout)  # Validate parse succeeds
                return True
        except Exception as e:
            logger.debug(f"Apple Silicon powermetrics check failed: {e}")
        return False

    def _read_powermetrics_energy_j(self):
        """Reads a single CPU energy sample via ``powermetrics`` on Apple Silicon.

        Returns:
            float or None: CPU package energy in Joules for the 1-second
            sample window, or None if the read fails.
        """
        try:
            result = subprocess.run(
                ["sudo", "-n", "powermetrics", "--samplers", "cpu_power",
                 "-n", "1", "-i", "1000", "--format", "plist"],
                capture_output=True,
                timeout=4,
            )
            if result.returncode != 0 or not result.stdout:
                return None
            data = plistlib.loads(result.stdout)
            # 'CPU Energy (mJ)' is the total package energy for the sample
            # interval; convert millijoules → joules.
            cpu_mj = data.get("CPU Energy (mJ)")
            if cpu_mj is not None:
                return float(cpu_mj) / 1000.0
        except Exception as e:
            logger.debug(f"Apple Silicon energy read failed: {e}")
        return None

    def get_cpu_energy_j(self):
        """Reads the current CPU package energy counter in Joules.

        Tries RAPL first (Linux), then Apple Silicon powermetrics (macOS arm64).

        Returns:
            float: Current energy in Joules, or None if hardware is unavailable.
        """
        # --- RAPL path (Linux) -----------------------------------------------
        if self.rapl_available:
            try:
                rapl_path = "/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj"
                with open(rapl_path, "r") as f:
                    uj = int(f.read().strip())
                    return uj / 1_000_000.0
            except Exception as e:
                logger.debug(f"RAPL read failed: {e}")
                return None

        # --- Apple Silicon path (macOS arm64) --------------------------------
        if self.apple_silicon_available:
            return self._read_powermetrics_energy_j()

        return None

    def estimate_cpu_power_w(self, tdp, utilization_pct):
        """Advanced CPU power estimation based on Boavizta's non-linear curve.
        
        Unlike simple linear TDP multiplication (TDP * utilization), this model 
        accounts for baseline idle power and exponential load scaling.
        
        Args:
            tdp (float): Thermal Design Power in watts.
            utilization_pct (float): CPU load percentage (0-100).
            
        Returns:
            float: Estimated power draw in watts.
        """
        x = max(0.0, min(100.0, utilization_pct))
        
        # Piecewise linear interpolation of Boavizta generic workload ratios
        # Ratios (Load -> % of TDP): 0% -> 12%, 10% -> 32%, 50% -> 75%, 100% -> 102%
        if x < 10:
            ratio = 0.12 + (0.32 - 0.12) * (x / 10.0)
        elif x < 50:
            ratio = 0.32 + (0.75 - 0.32) * ((x - 10.0) / 40.0)
        else:
            ratio = 0.75 + (1.02 - 0.75) * ((x - 50.0) / 50.0)
            
        return tdp * ratio
