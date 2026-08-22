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


def test_accumulate_carbon_falls_back_to_sync_export_when_thread_pool_submit_fails():
    """Exporter dispatch should still work if the background pool cannot accept work."""
    eco = EcoTrace(quiet=True, check_updates=False)
    exporter = MagicMock()
    eco.add_exporter(exporter)

    with patch.object(eco._exporter_pool, "submit", side_effect=RuntimeError("pool closed")):
        eco._accumulate_carbon(
            carbon_emitted=0.005,
            func_name="test_function",
            duration=1.2,
        )

    exporter.export.assert_called_once_with(
        carbon_emitted=0.005,
        func_name="test_function",
        duration=1.2,
        region=eco.region_code,
        run_id=eco._run_id,
        run_label=eco._run_label,
    )

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

from ecotrace.exporters.webhook import WebhookExporter

@patch('requests.post')
def test_webhook_exporter_registration_and_export(mock_post):
    """Verify WebhookExporter attaches to EcoTrace and POSTs metrics successfully."""
    mock_post.return_value.status_code = 200

    eco = EcoTrace(quiet=True, check_updates=False)
    eco._run_id = "test_run_id"
    eco._run_label = "test_label"
    
    exporter = WebhookExporter(ecotrace_instance=eco, url="http://example.com/webhook", headers={"X-Test": "Value"})
    
    assert len(eco._exporters) == 1
    assert eco._exporters[0] is exporter
    
    eco.region_code = "US"
    eco._accumulate_carbon(
        carbon_emitted=0.005,
        func_name="test_function",
        duration=1.2
    )
    
    eco._exporter_pool.shutdown(wait=True)
    
    # Assert requests.post was called with the correct args
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "http://example.com/webhook"
    assert kwargs["headers"] == {"Content-Type": "application/json", "X-Test": "Value"}
    payload = kwargs["json"]
    assert payload["function"] == "test_function"
    assert payload["carbon_gco2"] == 0.005
    assert payload["duration_s"] == 1.2
    assert payload["region"] == "US"
    assert payload["run_id"] == "test_run_id"
    assert payload["run_label"] == "test_label"

def test_webhook_exporter_missing_dependency():
    """Verify WebhookExporter handles missing requests gracefully."""
    eco = EcoTrace(quiet=True, check_updates=False)
    
    with patch('ecotrace.exporters.webhook.requests', None):
        exporter = WebhookExporter(ecotrace_instance=eco, url="http://example.com")
        assert exporter.url is None
        exporter.export(0.5, "test", 1.0, "GLOBAL")


from ecotrace.exporters.cloud import CloudExporter

@patch('requests.Session.post')
def test_cloud_exporter_registration_and_export(mock_post):
    """Verify CloudExporter formats payload and sends X-EcoTrace-Key header."""
    mock_post.return_value.status_code = 202

    exporter = CloudExporter(api_key="eco_usr_testkey123")
    exporter.export(
        carbon_emitted=0.0042,
        func_name="test_cloud_func",
        duration=0.5,
        region="TR",
        run_id="run_123",
        run_label="test_label"
    )

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["function"] == "test_cloud_func"
    assert kwargs["json"]["carbon_gco2"] == 0.0042
    assert kwargs["json"]["region"] == "TR"
    assert kwargs["json"]["run_id"] == "run_123"
    assert exporter.session.headers["X-EcoTrace-Key"] == "eco_usr_testkey123"

def test_cloud_exporter_requires_key():
    """Verify CloudExporter raises ValueError when instantiated without a valid key."""
    with pytest.raises(ValueError):
        CloudExporter(api_key="")

def test_ecotrace_auto_registers_cloud_exporter():
    """Verify EcoTrace auto-registers CloudExporter when instantiated with eco_usr_ key."""
    eco = EcoTrace(api_key="eco_usr_valid123", quiet=True, check_updates=False)
    assert len(eco._exporters) == 1
    assert isinstance(eco._exporters[0], CloudExporter)
    assert eco._exporters[0].api_key == "eco_usr_valid123"


