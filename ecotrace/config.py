import os
import json

DEFAULT_GPU_TDP_INTEL_W = 15.0
DEFAULT_GPU_TDP_AMD_W = 75.0
DEFAULT_GPU_TDP_UNKNOWN_W = 100.0
DEFAULT_CARBON_INTENSITY = 475
DEFAULT_REGION = "GLOBAL"
USER_AGENT = "EcoTrace/0.7.1"

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
        from .logger import logger
        logger.warning(f"Invalid region code provided ({region_code!r}). Defaulting to {DEFAULT_REGION}.")
        return DEFAULT_REGION

    code = region_code.strip().upper()
    intensity_map = constants_data.get("CARBON_INTENSITY_MAP", {})

    if code not in intensity_map:
        from .logger import logger
        logger.warning(f"Unmapped region code '{code}'. Defaulting to {DEFAULT_REGION}.")
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


# ============================================================================
# Live Grid API — Electricity Maps Integration (v6.0)
# ============================================================================

# --- ISO 3166-1 Alpha-2 → Electricity Maps Zone ID mapping ------------------
# Maps standard country codes used by EcoTrace to the zone identifiers
# expected by the Electricity Maps API. Countries with multiple grids
# (e.g. US, CA, AU) default to a representative national zone.
ZONE_MAPPING = {
    "TR": "TR",       "DE": "DE",       "FR": "FR",
    "US": "US-MIDA-PJM",  "GB": "GB",  "IN": "IN-NO",
    "CN": "CN",       "AU": "AU-NSW",   "CA": "CA-ON",
    "BR": "BR-CS",    "JP": "JP-TK",    "KR": "KR",
    "NL": "NL",       "SE": "SE",       "NO": "NO-NO1",
    "PL": "PL",       "IT": "IT-NO",    "ES": "ES",
    "PT": "PT",       "BE": "BE",       "CH": "CH",
    "AT": "AT",       "FI": "FI",       "DK": "DK-DK1",
    "CZ": "CZ",       "HU": "HU",       "RO": "RO",
    "ZA": "ZA",       "MX": "MX",       "AR": "AR",
    "ID": "ID",       "MY": "MY-WM",    "TH": "TH",
    "PH": "PH",       "SG": "SG",       "NZ": "NZ-NZN",
    "EG": "EG",       "NG": "NG",       "IE": "IE",
    "IL": "IL",       "TW": "TW",       "AE": "AE",
    "CO": "CO",       "KE": "KE",       "CL": "CL",
    "GR": "GR",       "UA": "UA",
}

# --- API Configuration -------------------------------------------------------
# Developer Note: We chose Electricity Maps because they provide the most 
# scientifically rigorous grid data, even if it requires a manual API key.
# Accuracy over convenience.
ELECTRICITY_MAPS_API_URL = "https://api.electricitymaps.com/v3/carbon-intensity/latest"
GRID_API_REQUEST_TIMEOUT_S = 5  # Maximum wait for API response (seconds)
GRID_CACHE_TTL_S = 3600         # Cache duration: 1 hour (seconds)


def fetch_live_carbon_intensity(region_code, grid_api_key):
    """Fetches real-time carbon intensity from the Electricity Maps API.

    Queries the Electricity Maps ``/v3/carbon-intensity/latest`` endpoint
    for the specified region's current grid carbon intensity. The API
    requires a valid authentication token.

    This function is designed to be **fail-safe**: any network error,
    timeout, authentication failure, or malformed response will cause it
    to return None, allowing the caller to fall back to static data.

    Args:
        region_code: ISO 3166-1 alpha-2 country code (e.g. 'TR', 'DE').
            Converted to an Electricity Maps zone via ZONE_MAPPING.
        grid_api_key: Electricity Maps API authentication token.

    Returns:
        float or None: Real-time carbon intensity in gCO2eq/kWh if the
        API query succeeds, or None if any error occurs. The caller
        should fall back to static ``CARBON_INTENSITY_MAP`` values
        when None is returned.

    Example:
        >>> intensity = fetch_live_carbon_intensity("TR", "my-api-key")
        >>> if intensity is not None:
        ...     print(f"Live grid: {intensity} gCO2/kWh")
        ... else:
        ...     print("Using static fallback data")
    """
    if not grid_api_key:
        return None

    # Resolve the Electricity Maps zone identifier from ISO country code
    zone = ZONE_MAPPING.get(region_code.upper(), region_code.upper())

    try:
        import requests  # type: ignore
        response = requests.get(
            ELECTRICITY_MAPS_API_URL,
            headers={"auth-token": grid_api_key, "User-Agent": USER_AGENT},
            params={"zone": zone},
            timeout=GRID_API_REQUEST_TIMEOUT_S,
        )
        response.raise_for_status()

        data = response.json()
        intensity = data.get("carbonIntensity")

        # Validate that we got a usable numeric value
        if intensity is not None and isinstance(intensity, (int, float)) and intensity > 0:
            return float(intensity)

        return None

    except Exception:
        # Fail silently — live grid must never crash the application
        return None

def identify_user_region():
    """Attempts to auto-detect the user's current region via IP address."""
    try:
        import requests  # type: ignore
        api_url = "http://ip-api.com/json/?fields=countryCode"
        response = requests.get(api_url, headers={"User-Agent": USER_AGENT}, timeout=2)
        response.raise_for_status()
        data = response.json()
        return data.get("countryCode")
    except Exception:
        return None
