import os
import json

DEFAULT_GPU_TDP_INTEL_W = 15.0
DEFAULT_GPU_TDP_AMD_W = 75.0
DEFAULT_GPU_TDP_UNKNOWN_W = 100.0
DEFAULT_CARBON_INTENSITY = 475
DEFAULT_REGION = "TR"

def load_constants(json_path):
    """Loads constants from the JSON configuration file.

    Args:
        json_path (str): Absolute or relative path to the constants.json file.

    Returns:
        dict: Parsed JSON data, or an empty dictionary if loading fails.
    """
    try:
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def validate_region_code(region_code, constants_data):
    """Validates the provided region code against known carbon mappings.

    Args:
        region_code (str): The ISO 3166-1 alpha-2 country code.
        constants_data (dict): Data dictionary containing 'CARBON_INTENSITY_MAP'.

    Returns:
        str: Validated uppercase region code, or DEFAULT_REGION if invalid.
    """
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
    """Resolves the carbon intensity value for the given region.

    Args:
        region_code (str): The validated region code string.
        constants_data (dict): Data dictionary containing 'CARBON_INTENSITY_MAP'.

    Returns:
        float: Carbon intensity value in gCO2/kWh.
    """
    return (
        constants_data
        .get("CARBON_INTENSITY_MAP", {})
        .get(region_code, DEFAULT_CARBON_INTENSITY)
    )

def load_gpu_tdp_defaults(constants_data):
    """Retrieves default GPU TDP estimations based on vendor.

    Args:
        constants_data (dict): Data dictionary containing 'GPU_TDP_DEFAULTS'.

    Returns:
        dict: Mapping of vendor names (intel, amd, unknown) to their respective TDPs in watts.
    """
    return constants_data.get("GPU_TDP_DEFAULTS", {
        "intel": DEFAULT_GPU_TDP_INTEL_W,
        "amd": DEFAULT_GPU_TDP_AMD_W,
        "unknown": DEFAULT_GPU_TDP_UNKNOWN_W,
    })
