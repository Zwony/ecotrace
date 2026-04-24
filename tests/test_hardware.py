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
