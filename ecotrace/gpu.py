def get_gpu_info(gpu_index, gpu_tdp_defaults):
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
    WATTS_PER_KILOWATT = 1000
    try:
        import nvidia_ml_py as pynvml  # type: ignore
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
        name = pynvml.nvmlDeviceGetName(handle)
        display_name = "".join(c for c in name if ord(c) < 128).replace("(R)", "").replace("(TM)", "").replace("(r)", "").replace("(tm)", "")
        tdp = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / WATTS_PER_KILOWATT
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
                else:
                    return {"brand": display_name, "tdp": gpu_tdp_defaults.get("unknown", 100.0), "type": "unknown", "handle": None}
    except Exception:
        pass

    return None

def get_gpu_power_w(gpu_info):
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
        # NVML returns power in milliwatts
        power_mw = pynvml.nvmlDeviceGetPowerUsage(gpu_info["handle"])
        return power_mw / 1000.0
    except Exception:
        return None
