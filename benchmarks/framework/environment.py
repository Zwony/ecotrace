"""
Environment Snapshot Module
============================
Captures a complete, reproducible fingerprint of the system under test.
Every benchmark report embeds this snapshot so results can be independently verified.
"""

import os
import sys
import json
import platform
import datetime
from typing import Dict, Any, Optional


def _safe_import_version(module_name: str) -> Optional[str]:
    """Safely retrieves the version of an installed module."""
    try:
        mod = __import__(module_name)
        return getattr(mod, "__version__", "unknown")
    except ImportError:
        return None


def _get_cpu_info_dict() -> Dict[str, Any]:
    """Extracts CPU metadata via py-cpuinfo and psutil."""
    info: Dict[str, Any] = {
        "brand": "Unknown",
        "arch": platform.machine(),
        "logical_cores": os.cpu_count() or 0,
        "physical_cores": None,
    }
    try:
        import psutil
        info["physical_cores"] = psutil.cpu_count(logical=False)
    except ImportError:
        pass

    try:
        import cpuinfo
        ci = cpuinfo.get_cpu_info()
        info["brand"] = ci.get("brand_raw", info["brand"])
        info["hz_advertised"] = ci.get("hz_advertised_friendly")
    except ImportError:
        pass

    return info


def _get_memory_info() -> Dict[str, Any]:
    """Returns total and available memory in GB."""
    try:
        import psutil
        vm = psutil.virtual_memory()
        return {
            "total_gb": round(vm.total / (1024 ** 3), 2),
            "available_gb": round(vm.available / (1024 ** 3), 2),
        }
    except ImportError:
        return {"total_gb": None, "available_gb": None}


def _get_gpu_info() -> Optional[Dict[str, Any]]:
    """Detects NVIDIA GPU via pynvml (optional)."""
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode("utf-8")
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return {
            "name": name,
            "memory_total_gb": round(mem.total / (1024 ** 3), 2),
            "driver_version": pynvml.nvmlSystemGetDriverVersion(),
        }
    except Exception:
        return None


def _detect_power_source() -> str:
    """Detects whether the machine is on AC power or battery."""
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery is None:
            return "AC (no battery)"
        return "AC" if battery.power_plugged else "Battery"
    except Exception:
        return "unknown"


class EnvironmentSnapshot:
    """Immutable snapshot of the test environment at benchmark start time.

    Usage::

        snap = EnvironmentSnapshot()
        snap.save("results/env.json")
        print(snap.to_dict())
    """

    def __init__(self, extra_packages: Optional[list] = None):
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.python_version = sys.version
        self.python_impl = platform.python_implementation()
        self.os_name = platform.system()
        self.os_release = platform.release()
        self.os_version = platform.version()
        self.machine = platform.machine()
        self.cpu_info = _get_cpu_info_dict()
        self.memory = _get_memory_info()
        self.gpu_info = _get_gpu_info()
        self.power_source = _detect_power_source()

        # Package versions relevant to benchmarks
        core_packages = ["ecotrace", "numpy", "pandas", "polars", "torch",
                         "tensorflow", "psutil", "matplotlib"]
        if extra_packages:
            core_packages.extend(extra_packages)

        self.package_versions: Dict[str, Optional[str]] = {}
        for pkg in sorted(set(core_packages)):
            ver = _safe_import_version(pkg)
            if ver is not None:
                self.package_versions[pkg] = ver

    def to_dict(self) -> Dict[str, Any]:
        """Returns the snapshot as a plain dictionary."""
        return {
            "timestamp": self.timestamp,
            "python": {
                "version": self.python_version,
                "implementation": self.python_impl,
            },
            "os": {
                "name": self.os_name,
                "release": self.os_release,
                "version": self.os_version,
            },
            "cpu": self.cpu_info,
            "memory": self.memory,
            "gpu": self.gpu_info,
            "power_source": self.power_source,
            "packages": self.package_versions,
        }

    def save(self, filepath: str) -> None:
        """Persists the snapshot to a JSON file."""
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def __repr__(self) -> str:
        cpu = self.cpu_info.get("brand", "Unknown")
        mem = self.memory.get("total_gb", "?")
        return f"<EnvironmentSnapshot cpu='{cpu}' ram={mem}GB os='{self.os_name}'>"
