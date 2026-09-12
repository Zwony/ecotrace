from unittest.mock import MagicMock, patch

from ecotrace.ram import RAM_WATT_FACTORS, _classify_ram_type, get_ram_info


def test_classify_ram_type_ddr3_thresholds():
    """Verify DDR3 classification for clock speeds up to 2133 MHz."""
    assert _classify_ram_type(800) == "DDR3"
    assert _classify_ram_type(1066) == "DDR3"
    assert _classify_ram_type(1333) == "DDR3"
    assert _classify_ram_type(1600) == "DDR3"
    assert _classify_ram_type(1866) == "DDR3"
    assert _classify_ram_type(2133) == "DDR3"
    assert _classify_ram_type(2200) == "DDR3"
    assert _classify_ram_type(2399) == "DDR3"


def test_classify_ram_type_ddr4_thresholds():
    """Verify DDR4 classification for clock speeds between 2400 MHz and 4799 MHz."""
    assert _classify_ram_type(2400) == "DDR4"
    assert _classify_ram_type(2666) == "DDR4"
    assert _classify_ram_type(2933) == "DDR4"
    assert _classify_ram_type(3200) == "DDR4"
    assert _classify_ram_type(3600) == "DDR4"
    assert _classify_ram_type(4000) == "DDR4"
    assert _classify_ram_type(4799) == "DDR4"


def test_classify_ram_type_ddr5_thresholds():
    """Verify DDR5 classification for clock speeds 4800 MHz and above."""
    assert _classify_ram_type(4800) == "DDR5"
    assert _classify_ram_type(5200) == "DDR5"
    assert _classify_ram_type(5600) == "DDR5"
    assert _classify_ram_type(6000) == "DDR5"
    assert _classify_ram_type(6400) == "DDR5"
    assert _classify_ram_type(7200) == "DDR5"


def test_ram_watt_factors_has_ddr3():
    """Verify RAM_WATT_FACTORS includes DDR3 with documented 0.500 W/GB rating."""
    assert "DDR3" in RAM_WATT_FACTORS
    assert RAM_WATT_FACTORS["DDR3"] == 0.500
    assert RAM_WATT_FACTORS["DDR4"] == 0.375
    assert RAM_WATT_FACTORS["DDR5"] == 0.285


def test_ram_info_windows_ddr3_detection():
    """Simulate Windows CIM reporting DDR3 speed (1600 MHz)."""
    mock_vm = MagicMock()
    mock_vm.total = 8 * (1024**3)
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = "1600\n"

    with patch("os.name", "nt"), \
         patch("psutil.virtual_memory", return_value=mock_vm), \
         patch("subprocess.run", return_value=mock_res):
        info = get_ram_info()
        assert info["total_gb"] == 8.0
        assert info["type"] == "DDR3"
        assert info["speed_mhz"] == "1600"


def test_ram_info_linux_ddr3_detection():
    """Simulate Linux dmidecode reporting DDR3 speed (1333 MHz)."""
    mock_vm = MagicMock()
    mock_vm.total = 4 * (1024**3)
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = "Memory Device\n\tSpeed: 1333 MHz\n\tManufacturer: Kingston\n"

    with patch("os.name", "posix"), \
         patch("psutil.virtual_memory", return_value=mock_vm), \
         patch("subprocess.run", return_value=mock_res):
        info = get_ram_info()
        assert info["total_gb"] == 4.0
        assert info["type"] == "DDR3"
        assert info["speed_mhz"] == "1333"


def test_ram_info_unrecognized_speed_defaults_to_ddr4():
    """Verify fallback to safe default (DDR4) when speed cannot be determined."""
    mock_vm = MagicMock()
    mock_vm.total = 16 * (1024**3)
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = "Not A Number\n"

    with patch("os.name", "nt"), \
         patch("psutil.virtual_memory", return_value=mock_vm), \
         patch("subprocess.run", return_value=mock_res):
        info = get_ram_info()
        assert info["type"] == "DDR4"
        assert info["speed_mhz"] == "Unknown"
