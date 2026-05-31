import os
import csv
import pytest
from unittest.mock import patch, MagicMock
from ecotrace.ml import EcoTraceML, ecotrace_ml

def test_ecotraceml_context_manager(tmp_path):
    # Mocking external calls to keep tests isolated and hardware-independent
    mock_gpu_info = {"brand": "Test GPU", "tdp": 200.0, "type": "nvidia", "handle": MagicMock()}
    
    with patch("ecotrace.ml.get_gpu_info", return_value=mock_gpu_info), \
         patch("ecotrace.ml.get_gpu_power_w", return_value=100.0), \
         patch("ecotrace.ml.create_gpu_usage_chart", return_value="dummy_chart.png"), \
         patch("ecotrace.ml.generate_pdf_report") as mock_pdf_report, \
         patch("os.path.exists", return_value=True), \
         patch("shutil.copy"), \
         patch("os.remove"):
         
        with EcoTraceML(model_name="test_model", gpu_index=0, sample_interval=0.1) as tracker:
            assert tracker.model_name == "test_model"
            assert tracker.sample_interval == 0.1
            assert tracker.is_running is True
            # Let it run briefly
            import time
            time.sleep(0.25)
            
        assert tracker.is_running is False
        assert tracker.total_gpu_energy_joules > 0.0
        # Ensure pdf generation is attempted
        mock_pdf_report.assert_called_once()

def test_ecotraceml_decorator():
    mock_gpu_info = {"brand": "Test GPU", "tdp": 250.0, "type": "nvidia", "handle": MagicMock()}
    
    with patch("ecotrace.ml.get_gpu_info", return_value=mock_gpu_info), \
         patch("ecotrace.ml.get_gpu_power_w", return_value=120.0), \
         patch("ecotrace.ml.create_gpu_usage_chart", return_value="dummy_chart.png"), \
         patch("ecotrace.ml.generate_pdf_report"), \
         patch("os.path.exists", return_value=True), \
         patch("shutil.copy"), \
         patch("os.remove"):
         
        @ecotrace_ml(model_name="dec_model", gpu_index=0, sample_interval=0.05)
        def dummy_training():
            import time
            time.sleep(0.15)
            return "finished"
            
        res = dummy_training()
        assert res == "finished"

def test_ecotraceml_simulation_fallback():
    # If get_gpu_info returns None (no GPU detected), it should run in simulation mode
    with patch("ecotrace.ml.get_gpu_info", return_value=None), \
         patch("ecotrace.ml.get_gpu_power_w", return_value=None), \
         patch("ecotrace.ml.create_gpu_usage_chart", return_value=None), \
         patch("ecotrace.ml.generate_pdf_report"), \
         patch("os.path.exists", return_value=False):
         
        with EcoTraceML(model_name="sim_model", gpu_index=0, sample_interval=0.05) as tracker:
            import time
            time.sleep(0.15)
            
        assert tracker.total_gpu_energy_joules > 0.0
