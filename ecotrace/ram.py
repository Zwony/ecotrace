import os
import psutil
import subprocess

RAM_WATT_FACTORS = {
    'DDR4': 0.375,
    'DDR5': 0.285
}

def _parse_dmidecode_output(stdout):
    for line in stdout.split('\n'):
        if 'Speed:' in line and 'MHz' in line:
            speed_str = line.split(':')[1].strip().replace('MHz', '').strip()
            if speed_str and speed_str.isdigit():
                return int(speed_str)
    return None

def get_ram_info():
    """Detects RAM specifications including type, speed, and total capacity.

    Performs OS-specific detection using PowerShell CIM on Windows and dmidecode on Linux to
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
                [
                    'powershell', '-NoProfile', '-Command',
                    '(Get-CimInstance Win32_PhysicalMemory | '
                    'Select-Object -ExpandProperty Speed | '
                    'Where-Object { $_ -gt 0 } | Select-Object -First 1)'
                ],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                speed_str = result.stdout.strip()
                if speed_str and speed_str.isdigit():
                    speed_mhz = int(speed_str)
                    ram_speed = str(speed_mhz)
                    ram_type = 'DDR5' if speed_mhz >= 4800 else 'DDR4'
        else:
            speed_mhz = None
            for use_sudo in (False, True):
                cmd = ['dmidecode', '-t', 'memory']
                if use_sudo:
                    cmd = ['sudo', '-n'] + cmd
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    speed_mhz = _parse_dmidecode_output(result.stdout)
                    if speed_mhz is not None:
                        break
            if speed_mhz is not None:
                ram_speed = str(speed_mhz)
                ram_type = 'DDR5' if speed_mhz >= 4800 else 'DDR4'
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, PermissionError, FileNotFoundError):
        pass

    return {
        'total_gb': total_ram_gb,
        'type': ram_type,
        'speed_mhz': ram_speed
    }
