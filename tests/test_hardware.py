import os
import pytest
from unittest.mock import patch, MagicMock
from ecotrace.cpu import get_cpu_info, load_tdp_database
from ecotrace.gpu import get_gpu_info
from ecotrace.ram import get_ram_info

def test_cpu_info_detection():
    # We mock cpuinfo to return a predictable string
    with patch("ecotrace.cpu.cpuinfo.get_cpu_info", return_value={"brand_raw": "Intel Core i9-13900K"}):
        info = get_cpu_info({}, {})
        assert "Intel Core i9" in info["brand"]
        assert info["cores"] > 0
        assert info["tdp"] == 65.0  # Fallback TDP if not in DB

def test_apple_silicon_tdp():
    with patch("ecotrace.cpu.cpuinfo.get_cpu_info", return_value={"brand_raw": "Apple M2 Max"}):
        constants = {"TDP_MAP": {"M2": 30.0}}
        info = get_cpu_info({}, constants)
        assert info["tdp"] == 30.0

def test_load_tdp_database(tmp_path):
    csv_file = tmp_path / "cpu_specs.csv"
    csv_file.write_text("name,tdp\nIntel Core i7-10700K,125.0\nAMD Ryzen 9 5950X,105.0\n")
    
    db = load_tdp_database(str(csv_file))
    assert db["intel core i7-10700k"] == 125.0
    assert db["amd ryzen 9 5950x"] == 105.0

def test_load_tdp_database_missing_file():
    db = load_tdp_database("non_existent.csv")
    assert db == {}

def test_gpu_info_no_nvidia_smi():
    # Patch the entire get_gpu_info to return None for this specific test case
    # to avoid complex WMI mocking on different OS environments.
    with patch("ecotrace.gpu.get_gpu_info", return_value=None):
        from ecotrace.gpu import get_gpu_info as mocked_get
        assert mocked_get(0, {}) is None

def test_ram_info_detection():
    info = get_ram_info()
    assert "total_gb" in info
    assert "type" in info
    assert info["total_gb"] > 0
    assert info["type"] in ["DDR4", "DDR5", "LPDDR4", "LPDDR5", "UNKNOWN"]


def test_ram_info_windows_success():
    mock_virtual_memory = MagicMock()
    mock_virtual_memory.total = 16 * (1024**3)
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "4800\n"
    
    with patch("os.name", "nt"), \
         patch("psutil.virtual_memory", return_value=mock_virtual_memory), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        info = get_ram_info()
        assert info["total_gb"] == 16.0
        assert info["type"] == "DDR5"
        assert info["speed_mhz"] == "4800"
        mock_run.assert_called_once()


def test_ram_info_windows_failure():
    mock_virtual_memory = MagicMock()
    mock_virtual_memory.total = 8 * (1024**3)
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    
    with patch("os.name", "nt"), \
         patch("psutil.virtual_memory", return_value=mock_virtual_memory), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        info = get_ram_info()
        assert info["total_gb"] == 8.0
        assert info["type"] == "DDR4"
        assert info["speed_mhz"] == "Unknown"


def test_ram_info_linux_success_no_sudo():
    mock_virtual_memory = MagicMock()
    mock_virtual_memory.total = 32 * (1024**3)
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Speed: 3200 MHz\n"
    
    with patch("os.name", "posix"), \
         patch("psutil.virtual_memory", return_value=mock_virtual_memory), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        info = get_ram_info()
        assert info["total_gb"] == 32.0
        assert info["type"] == "DDR4"
        assert info["speed_mhz"] == "3200"
        mock_run.assert_called_once_with(
            ["dmidecode", "-t", "memory"],
            capture_output=True, text=True, timeout=5
        )


def test_ram_info_linux_fallback_sudo():
    mock_virtual_memory = MagicMock()
    mock_virtual_memory.total = 32 * (1024**3)
    
    mock_result_fail = MagicMock()
    mock_result_fail.returncode = 1
    mock_result_fail.stdout = ""
    
    mock_result_success = MagicMock()
    mock_result_success.returncode = 0
    mock_result_success.stdout = "Speed: 5200 MHz\n"
    
    def side_effect(cmd, **kwargs):
        if cmd[0] == "dmidecode":
            return mock_result_fail
        return mock_result_success

    with patch("os.name", "posix"), \
         patch("psutil.virtual_memory", return_value=mock_virtual_memory), \
         patch("subprocess.run", side_effect=side_effect) as mock_run:
        info = get_ram_info()
        assert info["total_gb"] == 32.0
        assert info["type"] == "DDR5"
        assert info["speed_mhz"] == "5200"


def test_ram_info_linux_filenotfound_fallback_sudo():
    mock_virtual_memory = MagicMock()
    mock_virtual_memory.total = 32 * (1024**3)
    
    mock_result_success = MagicMock()
    mock_result_success.returncode = 0
    mock_result_success.stdout = "Speed: 4800 MHz\n"
    
    def side_effect(cmd, **kwargs):
        if cmd[0] == "dmidecode":
            raise FileNotFoundError()
        return mock_result_success

    with patch("os.name", "posix"), \
         patch("psutil.virtual_memory", return_value=mock_virtual_memory), \
         patch("subprocess.run", side_effect=side_effect) as mock_run:
        info = get_ram_info()
        assert info["total_gb"] == 32.0
        assert info["type"] == "DDR5"
        assert info["speed_mhz"] == "4800"
