def get_gpu_info(gpu_index, gpu_tdp_defaults):
    """Detects GPU hardware and resolves TDP using a tri-vendor fallback chain."""
    WATTS_PER_KILOWATT = 1000
    try:
        import nvidia_ml_py as pynvml
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
