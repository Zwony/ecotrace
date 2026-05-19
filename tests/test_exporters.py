import pytest
from unittest.mock import MagicMock, patch
from ecotrace.core import EcoTrace
from ecotrace.exporters.otel import OTelExporter

def test_add_exporter_core_api():
    """Verify the core EcoTrace instance accepts and retains exporters."""
    eco = EcoTrace(quiet=True, check_updates=False)
    assert hasattr(eco, "_exporters")
    assert len(eco._exporters) == 0

    mock_exporter = MagicMock()
    eco.add_exporter(mock_exporter)
    assert len(eco._exporters) == 1
    assert eco._exporters[0] is mock_exporter

@patch('ecotrace.exporters.otel.metrics')
def test_otel_exporter_registration_and_export(mock_metrics):
    """Verify OTelExporter attaches to EcoTrace and exports metrics successfully."""
    # Setup mock meter and counter
    mock_meter = MagicMock()
    mock_counter = MagicMock()
    mock_metrics.get_meter.return_value = mock_meter
    mock_meter.create_counter.return_value = mock_counter

    eco = EcoTrace(quiet=True, check_updates=False)
    
    # Initialize exporter
    exporter = OTelExporter(ecotrace_instance=eco, meter_name="test.meter")
    
    # Assert registration
    assert len(eco._exporters) == 1
    assert eco._exporters[0] is exporter
    mock_metrics.get_meter.assert_called_once_with("test.meter")
    mock_meter.create_counter.assert_called_once()
    
    # Trigger export through core API simulation
    eco.region_code = "US"  # Mock region for test
    eco._accumulate_carbon(
        carbon_emitted=0.005,
        func_name="test_function",
        duration=1.2
    )
    
    # Wait for the background exporter thread to finish
    eco._exporter_pool.shutdown(wait=True)
    
    # Assert export was called
    mock_counter.add.assert_called_once_with(
        0.005, 
        attributes={
            "ecotrace.function": "test_function",
            "ecotrace.region": "US"
        }
    )

def test_otel_exporter_missing_dependency():
    """Verify OTelExporter handles missing opentelemetry gracefully."""
    eco = EcoTrace(quiet=True, check_updates=False)
    
    # Force metrics to be None as if ImportError occurred
    with patch('ecotrace.exporters.otel.metrics', None):
        exporter = OTelExporter(ecotrace_instance=eco)
        
        # Should not crash, just returns early with counter as None
        assert exporter._carbon_counter is None
        
        # Calling export should be a safe no-op
        exporter.export(0.5, "test", 1.0, "GLOBAL")

# /* --- Hybrid End of File / Dosya Sonu --- */ #
