import os
import sys
from typing import Any, Dict, List, Optional


def get_gpu_info(gpu_index: int, gpu_tdp_defaults: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Detects GPU hardware and resolves its power limit using a tri-vendor fallback chain.

    Initializes NVIDIA NVML for precision TDP tracking. If an NVIDIA GPU is not found,
    it falls back to WMI (Windows Management Instrumentation) to perform string-based
    matching and assigns default architectural estimated TDPs.

    Args:
        gpu_index (int): Zero-based index of the target GPU device to monitor.
        gpu_tdp_defaults (dict): Vendor mapping for missing hardware limits (Intel/AMD).

    Returns:
        dict or None: GPU metadata dictionary containing:
            - brand (str): Human-readable device name.
            - tdp (float): Power management limit in watts.
            - type (str): Vendor classifier ('nvidia', 'intel', 'amd', 'unknown').
            - handle (object): NVML hardware handle if available, otherwise None.
        Returns None if no GPU is detected.
    """
    MILLIWATTS_PER_WATT = 1000
    
    if sys.platform == "win32":
        possible_paths = [r"C:\Program Files\NVIDIA Corporation\NVSMI", r"C:\Windows\System32"]
        for p in possible_paths:
            if os.path.exists(p) and p not in os.environ["PATH"]:
                os.environ["PATH"] += os.path.pathsep + p

    try:
        import nvidia_ml_py as pynvml  # type: ignore
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
        name = pynvml.nvmlDeviceGetName(handle)
        
        if isinstance(name, bytes):
            name = name.decode("utf-8", errors="ignore")
            
        display_name = "".join(c for c in name if ord(c) < 128).strip()
        tdp = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / MILLIWATTS_PER_WATT
        
        return {"brand": display_name, "tdp": tdp, "type": "nvidia", "handle": handle}
    except Exception:
        pass

    try:
        import wmi
        w = wmi.WMI()
        for i, gpu in enumerate(w.Win32_VideoController()):
            if i == gpu_index:
                name = gpu.Name
                display_name = "".join(c for c in name if ord(c) < 128).replace("(R)", "").replace("(TM)", "").replace("(r)", "").replace("(tm)", "")
                if "intel" in name.lower():
                    return {"brand": display_name, "tdp": gpu_tdp_defaults.get("intel", 15.0), "type": "intel", "handle": None}
                elif "amd" in name.lower() or "radeon" in name.lower():
                    return {"brand": display_name, "tdp": gpu_tdp_defaults.get("amd", 75.0), "type": "amd", "handle": None}
                elif any(v in name.lower() for v in ("nvidia", "geforce", "quadro", "tesla", "rtx", "gtx")):
                    return {"brand": display_name, "tdp": gpu_tdp_defaults.get("nvidia", 150.0), "type": "nvidia", "handle": None}
                else:
                    return {"brand": display_name, "tdp": gpu_tdp_defaults.get("unknown", 100.0), "type": "unknown", "handle": None}
    except Exception:
        pass

    return None

def get_gpu_power_w(gpu_info: Optional[Dict[str, Any]]) -> Optional[float]:
    """Reads exact instantaneous GPU power usage in watts via NVML.
    
    Args:
        gpu_info (dict): The GPU metadata dictionary from get_gpu_info.
        
    Returns:
        float: Current power draw in watts, or None if unavailable/unsupported.
    """
    if not gpu_info or gpu_info.get("type") != "nvidia" or gpu_info.get("handle") is None:
        return None
    try:
        import nvidia_ml_py as pynvml  # type: ignore
        power_mw = pynvml.nvmlDeviceGetPowerUsage(gpu_info["handle"])
        return power_mw / 1000.0
    except Exception:
        return None


def get_all_gpu_info(gpu_tdp_defaults: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Detects all available GPUs and returns their metadata as a list.

    Enumerates all NVIDIA GPUs via NVML device count. Falls back to the
    WMI-based single-GPU detection path for non-NVIDIA systems.

    Args:
        gpu_tdp_defaults (dict): Vendor mapping for missing hardware limits.

    Returns:
        list[dict]: List of GPU metadata dictionaries, each containing:
            - brand (str): Human-readable device name.
            - tdp (float): Power management limit in watts.
            - type (str): Vendor classifier ('nvidia', 'intel', 'amd', 'unknown').
            - handle (object): NVML hardware handle if available, otherwise None.
            - index (int): Zero-based GPU index.
        Returns an empty list if no GPUs are detected.
    """
    MILLIWATTS_PER_WATT = 1000
    gpus = []

    if sys.platform == "win32":
        possible_paths = [r"C:\Program Files\NVIDIA Corporation\NVSMI", r"C:\Windows\System32"]
        for p in possible_paths:
            if os.path.exists(p) and p not in os.environ["PATH"]:
                os.environ["PATH"] += os.path.pathsep + p

    # --- NVML enumeration (NVIDIA) ---
    try:
        import nvidia_ml_py as pynvml  # type: ignore
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()

        for i in range(device_count):
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)

                if isinstance(name, bytes):
                    name = name.decode("utf-8", errors="ignore")

                display_name = "".join(c for c in name if ord(c) < 128).strip()
                tdp = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / MILLIWATTS_PER_WATT

                gpus.append({
                    "brand": display_name,
                    "tdp": tdp,
                    "type": "nvidia",
                    "handle": handle,
                    "index": i,
                })
            except Exception:
                continue

        if gpus:
            return gpus
    except Exception:
        pass

    # --- WMI fallback (Windows non-NVIDIA) ---
    try:
        import wmi
        w = wmi.WMI()
        for i, gpu in enumerate(w.Win32_VideoController()):
            name = gpu.Name
            display_name = "".join(
                c for c in name if ord(c) < 128
            ).replace("(R)", "").replace("(TM)", "").replace("(r)", "").replace("(tm)", "")

            if "intel" in name.lower():
                vendor_type = "intel"
                tdp = gpu_tdp_defaults.get("intel", 15.0)
            elif "amd" in name.lower() or "radeon" in name.lower():
                vendor_type = "amd"
                tdp = gpu_tdp_defaults.get("amd", 75.0)
            elif any(v in name.lower() for v in ("nvidia", "geforce", "quadro", "tesla", "rtx", "gtx")):
                vendor_type = "nvidia"
                tdp = gpu_tdp_defaults.get("nvidia", 150.0)
            else:
                vendor_type = "unknown"
                tdp = gpu_tdp_defaults.get("unknown", 100.0)

            gpus.append({
                "brand": display_name,
                "tdp": tdp,
                "type": vendor_type,
                "handle": None,
                "index": i,
            })
    except Exception:
        pass

    return gpus


def get_all_gpu_power_w(gpu_infos: Optional[List[Dict[str, Any]]]) -> Optional[float]:
    """Reads total instantaneous power usage across all GPUs in watts.

    Sums the power draw from all NVIDIA GPUs with valid NVML handles.
    Non-NVIDIA GPUs are excluded from power readings (they use TDP estimation).

    Args:
        gpu_infos (list[dict]): List of GPU metadata dictionaries from get_all_gpu_info.

    Returns:
        float or None: Total power draw in watts across all measurable GPUs,
            or None if no GPU supports power measurement.
    """
    if not gpu_infos:
        return None

    total_power = 0.0
    measured_any = False

    try:
        import nvidia_ml_py as pynvml  # type: ignore
    except ImportError:
        return None

    for gpu_info in gpu_infos:
        if gpu_info.get("type") != "nvidia" or gpu_info.get("handle") is None:
            continue
        try:
            power_mw = pynvml.nvmlDeviceGetPowerUsage(gpu_info["handle"])
            total_power += power_mw / 1000.0
            measured_any = True
        except Exception:
            continue

    return total_power if measured_any else None
