import os
import psutil
import subprocess

RAM_WATT_FACTORS = {
    'DDR4': 0.375,
    'DDR5': 0.285
}

def get_ram_info():
    """Detects RAM specifications including type, speed, and total capacity.

    Performs OS-specific detection using WMIC on Windows and dmidecode on Linux to
    retrieve the memory speed, which is used to classify the RAM type (DDR4 vs DDR5).

    Returns:
        dict: Dictionary containing:
            - total_gb (float): System total memory in gigabytes.
            - type (str): RAM generation ('DDR4' or 'DDR5').
            - speed_mhz (str): Active memory frequency, or 'Unknown'.
    """
    total_ram_gb = psutil.virtual_memory().total / (1024**3)
    
    ram_type = 'DDR4'
    ram_speed = 'Unknown'
    
    try:
        if os.name == 'nt':
            result = subprocess.run(
                ['wmic', 'memorychip', 'get', 'speed', '/value'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Speed=' in line:
                        speed_str = line.split('=')[1].strip()
                        if speed_str and speed_str.isdigit():
                            speed_mhz = int(speed_str)
                            ram_speed = str(speed_mhz)
                            ram_type = 'DDR5' if speed_mhz >= 4800 else 'DDR4'
                            break
        else:
            result = subprocess.run(
                ['sudo', 'dmidecode', '-t', 'memory'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Speed:' in line and 'MHz' in line:
                        speed_str = line.split(':')[1].strip().replace('MHz', '').strip()
                        if speed_str and speed_str.isdigit():
                            speed_mhz = int(speed_str)
                            ram_speed = str(speed_mhz)
                            ram_type = 'DDR5' if speed_mhz >= 4800 else 'DDR4'
                            break
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, PermissionError, FileNotFoundError):
        pass
    
    return {
        'total_gb': total_ram_gb,
        'type': ram_type,
        'speed_mhz': ram_speed
    }
