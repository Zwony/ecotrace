import os
import json
import csv
import time
import pytest
from unittest.mock import patch, MagicMock
from ecotrace.core import EcoTrace

@pytest.fixture
def ecotrace_instance():
    # Use quiet=True and check_updates=False to keep tests fast and clean
    return EcoTrace(region_code="US", check_updates=False, quiet=True)

def test_ecotrace_initialization(ecotrace_instance):
    assert ecotrace_instance.region_code == "US"
    assert ecotrace_instance.total_carbon == 0.0
    assert ecotrace_instance.gpu_index == 0

def test_export_json_creates_file(ecotrace_instance, tmp_path):
    json_path = tmp_path / "test_report.json"
    csv_path = tmp_path / "dummy_log.csv"
    
    # Create a dummy CSV to be parsed
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Function", "Duration(s)", "Carbon(gCO2)", "Region", "AvgCPU(%)", "FilePath", "Line"])
        writer.writerow(["2026-04-23 12:00:00", "test_func", "1.5", "0.05", "US", "50.0", "test.py", "10"])

    ecotrace_instance.export_json(filename=str(json_path), csv_path=str(csv_path))
    
    assert os.path.exists(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert "meta" in data
    assert "measurements" in data
    assert "summary" in data
    assert len(data["measurements"]) == 1
    assert data["measurements"][0]["function"] == "test_func"
    assert data["summary"]["total_carbon_gco2"] == 0.05

def test_export_json_handles_missing_csv(ecotrace_instance, tmp_path):
    json_path = tmp_path / "empty_report.json"
    ecotrace_instance.export_json(filename=str(json_path), csv_path="non_existent.csv")
    
    assert os.path.exists(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data["measurements"]) == 0
    assert data["summary"]["total_carbon_gco2"] == 0.0

def test_sync_measure_execution(ecotrace_instance):
    def dummy_workload():
        return 42
        
    result = ecotrace_instance.measure(dummy_workload)
    assert result["result"] == 42
    assert "func_name" in result
    assert "carbon" in result
    assert result["func_name"] == "dummy_workload"

def test_async_measure_execution(ecotrace_instance):
    import asyncio
    async def async_dummy():
        await asyncio.sleep(0.01)
        return "async_done"
        
    result = asyncio.run(ecotrace_instance.measure_async(async_dummy))
    assert result["result"] == "async_done"
    assert result["func_name"] == "async_dummy"

def test_track_decorator(ecotrace_instance):
    @ecotrace_instance.track
    def decorated_func():
        return 100
        
    assert decorated_func() == 100

def test_track_block_context_manager(ecotrace_instance):
    initial_carbon = ecotrace_instance.total_carbon
    with ecotrace_instance.track_block("test_block"):
        _ = [x * 2 for x in range(1000)]
    assert ecotrace_instance.total_carbon >= initial_carbon

def test_csv_logging_does_not_crash_on_error(ecotrace_instance):
    # Pass an invalid file path that raises an OSError to ensure the try/except catches it
    with patch("builtins.open", side_effect=OSError("Permission denied")):
        # This should log a warning but not raise an exception
        ecotrace_instance._log_to_csv("test_func", 1.0, 0.01)

def test_pause_resume(ecotrace_instance):
    assert not ecotrace_instance._paused
    ecotrace_instance.pause()
    assert ecotrace_instance._paused
    
    # Test that _accumulate_carbon returns immediately when paused
    initial_carbon = ecotrace_instance.total_carbon
    ecotrace_instance._accumulate_carbon(0.5, "paused_func", 1.0)
    assert ecotrace_instance.total_carbon == initial_carbon
    
    ecotrace_instance.resume()
    assert not ecotrace_instance._paused
    
    ecotrace_instance._accumulate_carbon(0.5, "resumed_func", 1.0)
    assert ecotrace_instance.total_carbon == initial_carbon + 0.5

def test_async_measure_hotspot_metadata(ecotrace_instance):
    import asyncio
    async def async_dummy():
        return 42
        
    with patch.object(ecotrace_instance, "_log_to_csv") as mock_log:
        asyncio.run(ecotrace_instance.measure_async(async_dummy))
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert args[0] == "async_dummy"
        assert args[4] is not None
        assert args[4].endswith("test_core.py")
        assert args[5] is not None

def test_track_block_exception_safety(ecotrace_instance):
    """Verify track_block registers metrics even when wrapped block raises an exception."""
    initial_calls = ecotrace_instance._tracked_functions_count
    try:
        with ecotrace_instance.track_block("test_failing_block"):
            raise ValueError("Deliberate failure inside track_block")
    except ValueError:
        pass
    
    assert ecotrace_instance._tracked_functions_count == initial_calls + 1

def test_generate_pdf_report_with_3_tuples(ecotrace_instance, tmp_path):
    """Verify generate_pdf_report successfully processes 3-tuple GPU samples."""
    pdf_path = tmp_path / "test_report.pdf"
    
    # 3-tuples (timestamp, utilization, power) as stored in core monitor
    gpu_samples = [(time.time() - 2, 5.0, 50.0), (time.time() - 1, 10.0, 55.0)]
    
    # Mock create_gpu_usage_chart and create_cpu_usage_chart to prevent actual chart rendering/saving
    with patch("ecotrace.report.create_gpu_usage_chart", return_value=None), \
         patch("ecotrace.report.create_cpu_usage_chart", return_value=None):
        ecotrace_instance.generate_pdf_report(filename=str(pdf_path), gpu_samples=gpu_samples)
        
    assert os.path.exists(pdf_path)

def test_django_middleware_naming_compatibility():
    """Verify that both class names are importable and reference the same class."""
    from ecotrace.middleware.django import EcoTraceDjangoMiddleware, EcoTraceMiddleware
    assert EcoTraceDjangoMiddleware is EcoTraceMiddleware


