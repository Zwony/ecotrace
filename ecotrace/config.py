import os
import json

DEFAULT_GPU_TDP_INTEL_W = 15.0
DEFAULT_GPU_TDP_AMD_W = 75.0
DEFAULT_GPU_TDP_UNKNOWN_W = 100.0
DEFAULT_CARBON_INTENSITY = 475
DEFAULT_REGION = "TR"

def load_constants(json_path):
    try:
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def validate_region_code(region_code, constants_data):
    if not isinstance(region_code, str) or not region_code.strip():
        print(f"[EcoTrace] WARNING: Invalid region_code={region_code!r}, defaulting to '{DEFAULT_REGION}'.")
        return DEFAULT_REGION

    code = region_code.strip().upper()
    intensity_map = constants_data.get("CARBON_INTENSITY_MAP", {})

    if code not in intensity_map:
        print(f"[EcoTrace] WARNING: Unknown region '{code}', defaulting to '{DEFAULT_REGION}'.")
        return DEFAULT_REGION
    return code

def resolve_carbon_intensity(region_code, constants_data):
    return (
        constants_data
        .get("CARBON_INTENSITY_MAP", {})
        .get(region_code, DEFAULT_CARBON_INTENSITY)
    )

def load_gpu_tdp_defaults(constants_data):
    return constants_data.get("GPU_TDP_DEFAULTS", {
        "intel": DEFAULT_GPU_TDP_INTEL_W,
        "amd": DEFAULT_GPU_TDP_AMD_W,
        "unknown": DEFAULT_GPU_TDP_UNKNOWN_W,
    })
