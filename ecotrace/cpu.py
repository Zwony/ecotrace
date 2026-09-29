import os
import csv
import re
import psutil
import functools
import cpuinfo

@functools.lru_cache(maxsize=1)
def fetch_raw_cpu_info():
    """Retrieves raw CPU information bounding to py-cpuinfo caching.

    Returns:
        dict: Standardized CPU properties including architecture and physical identifiers.
    """
    return cpuinfo.get_cpu_info()

def load_tdp_database(csv_path):
    """Parses the Boavizta CPU specification dataset into a TDP lookup table.

    Args:
        csv_path (str): File system path targeting 'cpu_data.csv'.

    Returns:
        dict: Hash map linking lowercase exact CPU model strings to their float TDP values.
    """
    tdp_dict = {}
    if not os.path.exists(csv_path):
        return tdp_dict
    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                m_name = row.get('name', '').lower().strip()
                tdp_val = row.get('tdp')
                if m_name and tdp_val:
                    try:
                        tdp_dict[m_name] = float(tdp_val)
                    except ValueError:
                        continue
    except Exception:
        pass
    return tdp_dict

def get_cpu_info(tdp_db, constants_data=None):
    """Detects CPU hardware and resolves Thermal Design Power (TDP) in watts.

    Matches available processor strings against the verified CPU specification
    database (including Apple Silicon, Intel, AMD), with sensible defaults.

    Args:
        tdp_db (dict): Generated dictionary matching CPU hardware to known TDPs.
        constants_data (dict, optional): Application-wide constant configurations (kept for backward compatibility).

    Returns:
        dict: CPU characteristics comprising:
            - brand (str): Cleaned display name for the physical CPU.
            - cores (int): Count of logical processing threads utilizing the OS scheduler.
            - tdp (float): Assigned structural TDP boundary in watts.
    """
    info = fetch_raw_cpu_info()
    brand = info.get("brand_raw", "Unknown CPU")
    
    display_brand = "".join(c for c in brand if ord(c) < 128).replace("(R)", "").replace("(TM)", "").replace("(r)", "").replace("(tm)", "")
    
    clean_brand = brand.lower()
    clean_brand = clean_brand.replace("(r)", "").replace("(tm)", "")
    clean_brand = re.sub(r'\d+th\s+gen', '', clean_brand)
    clean_brand = " ".join(clean_brand.split())

    clean_brand_search = clean_brand.replace(" cpu ", " ").replace(" processor", "")
    clean_brand_search = " ".join(clean_brand_search.split())

    found_tdp = None
    if clean_brand in tdp_db:
        found_tdp = tdp_db[clean_brand]
    elif clean_brand_search in tdp_db:
        found_tdp = tdp_db[clean_brand_search]
    else:
        sorted_models = sorted(tdp_db.items(), key=lambda x: len(x[0]), reverse=True)
        for model_name, tdp in sorted_models:
            if len(model_name) > 3 and (model_name in clean_brand_search or clean_brand_search in model_name):
                found_tdp = tdp
                break

    if found_tdp is None:
        # Fallback based on architecture
        found_tdp = 25.0 if "apple" in clean_brand else 65.0

    return {"brand": display_brand, "cores": psutil.cpu_count(logical=True), "tdp": float(found_tdp)}
