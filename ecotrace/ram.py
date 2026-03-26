import os
import psutil
import subprocess

# RAM power consumption factors by type (Watts per GB)
RAM_WATT_FACTORS = {
    'DDR4': 0.375,  # DDR4 average power consumption per GB
    'DDR5': 0.285   # DDR5 is more efficient (lower power per GB)
}

def get_ram_info():
    """Detects RAM specifications including type, speed, and total capacity."""
    
    # Get total RAM from psutil (cross-platform)
    total_ram_gb = psutil.virtual_memory().total / (1024**3)
    
    # Initialize with fallback values
    ram_type = 'DDR4'  # Default fallback
    ram_speed = 'Unknown'
    
    try:
        if os.name == 'nt':  # Windows
            # Use WMIC to get RAM speed
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
                            # Classify RAM type based on speed
                            ram_type = 'DDR5' if speed_mhz >= 4800 else 'DDR4'
                            break
        else:  # Linux
            # Try dmidecode for detailed RAM info
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
        # Fallback to default values if any error occurs
        pass
    
    return {
        'total_gb': total_ram_gb,
        'type': ram_type,
        'speed_mhz': ram_speed
    }
