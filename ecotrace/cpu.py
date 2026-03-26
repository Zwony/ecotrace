import os
import csv
import re
import psutil
import functools
import cpuinfo

@functools.lru_cache(maxsize=1)
def fetch_raw_cpu_info():
    """Retrieves raw CPU information via py-cpuinfo."""
    return cpuinfo.get_cpu_info()

def load_tdp_database(csv_path):
    """Parses the Boavizta CPU spec CSV into a TDP lookup dictionary."""
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
    """Detects CPU hardware and resolves TDP using a multi-source lookup chain."""
    info = cpuinfo.get_cpu_info()
    brand = info.get("brand_raw", "Unknown CPU")
    
    # Clean brand string for matching, but keep a display version
    display_brand = "".join(c for c in brand if ord(c) < 128).replace("(R)", "").replace("(TM)", "").replace("(r)", "").replace("(tm)", "")
    
    clean_brand = brand.lower()
    clean_brand = clean_brand.replace("(r)", "").replace("(tm)", "")
    clean_brand = re.sub(r'\d+th\s+gen', '', clean_brand)
    clean_brand = " ".join(clean_brand.split())

    # Apple Silicon M-series detection
    if "apple" in clean_brand:
        found_tdp = 25.0  # M-series laptop-class average TDP fallback
        tdp_map = constants_data.get("TDP_MAP", {})
        for m_chip in ["m4", "m3", "m2", "m1"]:
            if m_chip in clean_brand:
                found_tdp = tdp_map.get(m_chip.upper(), 25.0)
                break
    else:
        # Intel/AMD CSV database lookup
        found_tdp = 65.0  # Common mid-range desktop TDP fallback

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
