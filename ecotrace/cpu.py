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
        csv_path (str): File system path targeting the Boavizta 'cpu_specs.csv'.

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

def get_cpu_info(tdp_db, constants_data):
    """Detects CPU hardware and resolves Thermal Design Power using a multi-source chain.

    Matches available chip strings strictly against Apple Silicon static definitions
    first, before fuzzy matching against the Boavizta hardware database for x86 chips.

    Args:
        tdp_db (dict): Generated dictionary matching CPU hardware to known TDPs.
        constants_data (dict): Application-wide constant configurations containing 'TDP_MAP'.

    Returns:
        dict: CPU characteristics comprising:
            - brand (str): ASCII-cleaned display name for the physical CPU.
            - cores (int): Count of logical processing threads utilizing the OS scheduler.
            - tdp (float): Assigned structural TDP boundary in watts.
    """
    info = cpuinfo.get_cpu_info()
    brand = info.get("brand_raw", "Unknown CPU")
    
    display_brand = "".join(c for c in brand if ord(c) < 128).replace("(R)", "").replace("(TM)", "").replace("(r)", "").replace("(tm)", "")
    
    clean_brand = brand.lower()
    clean_brand = clean_brand.replace("(r)", "").replace("(tm)", "")
    clean_brand = re.sub(r'\d+th\s+gen', '', clean_brand)
    clean_brand = " ".join(clean_brand.split())

    if "apple" in clean_brand:
        found_tdp = 25.0
        tdp_map = constants_data.get("TDP_MAP", {})
        for m_chip in ["m4", "m3", "m2", "m1"]:
            if m_chip in clean_brand:
                found_tdp = tdp_map.get(m_chip.upper(), 25.0)
                break
    else:
        found_tdp = 65.0
        if clean_brand in tdp_db:
            found_tdp = tdp_db[clean_brand]
        else:
            for model_name, tdp in tdp_db.items():
                if model_name == clean_brand:
                    found_tdp = tdp
                    break
                if clean_brand in model_name and len(clean_brand) > 10:
                    found_tdp = tdp
                    break

    return {"brand": display_brand, "cores": psutil.cpu_count(logical=True), "tdp": found_tdp}
