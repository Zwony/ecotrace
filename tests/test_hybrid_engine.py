import pytest
from ecotrace.hardware import HardwareMonitor

def test_hardware_monitor_initialization():
    """Verify that HardwareMonitor initializes correctly on the current platform."""
    monitor = HardwareMonitor()
    assert hasattr(monitor, "rapl_available")
    assert isinstance(monitor.rapl_available, bool)

def test_boavizta_estimation_curve():
    """Verify the non-linear Boavizta estimation logic."""
    monitor = HardwareMonitor()
    tdp = 100.0
    
    # Idle (0%): Should be around 12% of TDP
    idle_power = monitor.estimate_cpu_power_w(tdp, 0.0)
    assert 11.9 < idle_power < 12.1
    
    # High Load (100%): Should be around 102% of TDP
    max_power = monitor.estimate_cpu_power_w(tdp, 100.0)
    assert 101.9 < max_power < 102.1
    
    # Mid Load (50%): Should be around 75% of TDP
    mid_power = monitor.estimate_cpu_power_w(tdp, 50.0)
    assert 74.9 < mid_power < 75.1

def test_rapl_read_safety():
    """Ensure get_cpu_energy_j returns None or a float without crashing."""
    monitor = HardwareMonitor()
    energy = monitor.get_cpu_energy_j()
    if monitor.rapl_available:
        assert isinstance(energy, float)
    else:
        assert energy is None

def test_power_interpolation_smoothness():
    """Verify that the piecewise linear interpolation is continuous."""
    monitor = HardwareMonitor()
    tdp = 100.0
    
    # Check 10% boundary
    p9 = monitor.estimate_cpu_power_w(tdp, 9.9)
    p10 = monitor.estimate_cpu_power_w(tdp, 10.0)
    p11 = monitor.estimate_cpu_power_w(tdp, 10.1)
    assert p9 < p10 < p11
    
    # Check 50% boundary
    p49 = monitor.estimate_cpu_power_w(tdp, 49.9)
    p50 = monitor.estimate_cpu_power_w(tdp, 50.0)
    p51 = monitor.estimate_cpu_power_w(tdp, 51.0)
    assert p49 < p50 < p51
