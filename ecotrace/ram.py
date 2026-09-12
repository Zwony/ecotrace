import os
import subprocess

import psutil

RAM_WATT_FACTORS = {
    'DDR3': 0.500,
    'DDR4': 0.375,
    'DDR5': 0.285,
    'LPDDR4': 0.200,
    'LPDDR5': 0.150,
    'UNKNOWN': 0.375
}

def _classify_ram_type(speed_mhz):
    """Classifies RAM generation from clock speed in MHz.

    DDR3: 800, 1066, 1333, 1600, 1866, 2133 MHz (max 2133)
    DDR4: 2400, 2666, 2933, 3200, 3600 MHz (2400–4800)
    DDR5: 4800, 5200, 5600, 6000, 6400+ MHz (4800+)

    Args:
        speed_mhz (int): Memory clock speed in MHz.

    Returns:
        str: RAM generation string ('DDR3', 'DDR4', or 'DDR5').
    """
    if speed_mhz >= 4800:
        return 'DDR5'
    elif speed_mhz >= 2400:
        return 'DDR4'
    else:
        return 'DDR3'

def get_ram_info():
    """Detects RAM specifications including type, speed, and total capacity.

    Performs OS-specific detection using PowerShell/CIM on Windows and dmidecode
    on Linux to retrieve the memory speed, which is used to classify the RAM
    type (DDR3, DDR4, or DDR5).

    Returns:
        dict: Dictionary containing:
            - total_gb (float): System total memory in gigabytes.
            - type (str): RAM generation ('DDR3', 'DDR4', or 'DDR5').
            - speed_mhz (str): Active memory frequency, or 'Unknown'.
    """
    total_ram_gb = psutil.virtual_memory().total / (1024**3)
    
    ram_type = 'DDR4'
    ram_speed = 'Unknown'
    
    try:
        if os.name == 'nt':
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command',
                 'Get-CimInstance Win32_PhysicalMemory | Select-Object -ExpandProperty Speed'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    speed_str = line.strip()
                    if speed_str and speed_str.isdigit():
                        speed_mhz = int(speed_str)
                        ram_speed = str(speed_mhz)
                        ram_type = _classify_ram_type(speed_mhz)
                        break
        else:
            result = None
            try:
                result = subprocess.run(
                    ['dmidecode', '-t', 'memory'],
                    capture_output=True, text=True, timeout=5
                )
            except (FileNotFoundError, PermissionError):
                pass
            
            if result is None or result.returncode != 0 or not result.stdout.strip():
                try:
                    result = subprocess.run(
                        ['sudo', '-n', 'dmidecode', '-t', 'memory'],
                        capture_output=True, text=True, timeout=5
                    )
                except (FileNotFoundError, PermissionError):
                    pass

            if result is not None and result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Speed:' in line and 'MHz' in line:
                        speed_str = line.split(':')[1].strip().replace('MHz', '').strip()
                        if speed_str and speed_str.isdigit():
                            speed_mhz = int(speed_str)
                            ram_speed = str(speed_mhz)
                            ram_type = _classify_ram_type(speed_mhz)
                            break
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, PermissionError, FileNotFoundError):
        pass
    
    return {
        'total_gb': total_ram_gb,
        'type': ram_type,
        'speed_mhz': ram_speed
    }

