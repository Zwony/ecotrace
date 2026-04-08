import time
import pytest
import threading
from typing import Dict, Any

from ecotrace.core import EcoTrace

# --- Concurrency Limitations ---
# EcoTrace monitors at the process level. While internal registries are 
# thread-safe, parallel test execution (e.g., via pytest-xdist) will 
# lead to aggregated carbon metrics as concurrent tests share the 
# same process-scoped CPU resources.
# -------------------------------

def pytest_addoption(parser):
    """Add command-line flag to enable EcoTrace during tests."""
    group = parser.getgroup("ecotrace")
    group.addoption(
        "--ecotrace",
        action="store_true",
        default=False,
        help="Measure carbon footprint of tests using EcoTrace.",
    )

# Thread-safe storage for test results: nodeid -> dict(duration, carbon, ... )
test_emissions: Dict[str, Any] = {}
emissions_lock = threading.Lock()
ecotrace_instance: EcoTrace = None

def pytest_configure(config):
    """Initialize EcoTrace if the flag is enabled."""
    global ecotrace_instance
    if config.getoption("--ecotrace"):
        # Initialize quietly and suppress update checks for CI/CD compatibility
        ecotrace_instance = EcoTrace(quiet=True, check_updates=False)

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    """Wrap test execution for carbon metric resolution.
    
    Snapshots process-scoped CPU utilization across the execution 
    lifecycle of each pytest item.
    """
    global ecotrace_instance
    if not ecotrace_instance:
        yield
        return

    start_time = time.perf_counter()
    
    with ecotrace_instance.cpu_monitor():
        # Yield to let the actual test run (setup, call, teardown)
        yield
    
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    try:
        avg_cpu = ecotrace_instance._get_avg_cpu_in_range(start_time, end_time)
        carbon_emitted = ecotrace_instance._compute_carbon(
            ecotrace_instance.cpu_info['tdp'], avg_cpu, duration
        )
        
        # Guarded dictionary update for thread safety
        with emissions_lock:
            test_emissions[item.nodeid] = {
                "duration": duration,
                "carbon": carbon_emitted,
                "avg_cpu": avg_cpu
            }
            
        # Accumulate globally into the main CSV audit log if tracked
        ecotrace_instance._accumulate_carbon(carbon_emitted, item.name, duration, avg_cpu)
    except Exception:
        # Failsafe: don't break tests if carbon measurement hits an error
        pass

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print the carbon footprint summary at the end of the test session."""
    if not config.getoption("--ecotrace") or not test_emissions:
        return

    terminalreporter.section("EcoTrace: Carbon Infrastructure Audit", sep="=", bold=True)
    
    with emissions_lock:
        total_carbon = sum(data["carbon"] for data in test_emissions.values())
        total_duration = sum(data["duration"] for data in test_emissions.values())
        snapshot = sorted(test_emissions.items(), key=lambda x: x[1]["carbon"], reverse=True)
    
    terminalreporter.write_line(f"Total Test Suite Duration : {total_duration:.2f} s")
    terminalreporter.write_line(f"Total Carbon Emissions    : {total_carbon:.8f} gCO2")
    terminalreporter.write_line("")
    
    # Identify top 3 most consuming tests
    top_tests = snapshot[:3]
    
    if top_tests:
        terminalreporter.write_line("Top 3 Most Carbon-Heavy Tests:", bold=True)
        terminalreporter.write_line("-" * 60)
        for i, (test_name, data) in enumerate(top_tests, 1):
            terminalreporter.write_line(
                f"{i}. {test_name}\n"
                f"   [CO2: {data['carbon']:.8f} gCO2 | Duration: {data['duration']:.2f}s | CPU: {data['avg_cpu']:.1f}%]"
            )
        terminalreporter.write_line("-" * 60)
