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


def _post_one_measurement(mock_post, carbon_emitted=0.005, carbon_limit=None, **exporter_kwargs):
    """Send one measurement through a WebhookExporter and return the JSON body it POSTed."""
    mock_post.return_value.status_code = 200

    eco = EcoTrace(quiet=True, check_updates=False, carbon_limit=carbon_limit)
    eco.region_code = "US"
    WebhookExporter(ecotrace_instance=eco, url="http://example.com/webhook", **exporter_kwargs)

    eco._accumulate_carbon(carbon_emitted=carbon_emitted, func_name="test_function", duration=1.2)
    eco._exporter_pool.shutdown(wait=True)

    mock_post.assert_called_once()
    return mock_post.call_args.kwargs["json"]


@patch('requests.post')
def test_webhook_exporter_default_format_keeps_json_payload(mock_post):
    """Without a format, the payload is the same flat dict the exporter sent before the option existed."""
    payload = _post_one_measurement(mock_post)

    assert set(payload) == {"function", "carbon_gco2", "duration_s", "region", "run_id", "run_label"}
    assert payload["function"] == "test_function"
    assert payload["carbon_gco2"] == 0.005
    assert payload["duration_s"] == 1.2
    assert payload["region"] == "US"
    assert "embeds" not in payload
    assert "blocks" not in payload


@patch('requests.post')
def test_webhook_exporter_json_format_matches_default_payload(mock_post):
    """format="json" is accepted and sends the same payload as the default (run_id differs per EcoTrace)."""
    default_payload = _post_one_measurement(mock_post)
    mock_post.reset_mock()
    json_payload = _post_one_measurement(mock_post, format="json")

    default_payload.pop("run_id")
    json_payload.pop("run_id")
    assert json_payload == default_payload


@patch('requests.post')
def test_webhook_exporter_discord_sends_an_embed(mock_post):
    """format="discord" sends one embed with the function name, gCO2 and duration."""
    payload = _post_one_measurement(mock_post, format="discord")

    assert list(payload) == ["embeds"]
    assert len(payload["embeds"]) == 1
    embed = payload["embeds"][0]
    assert "test_function" in embed["title"]
    fields = {field["name"]: field["value"] for field in embed["fields"]}
    assert fields == {"Carbon": "0.005000 gCO2", "Duration": "1.20 s"}


@pytest.mark.parametrize("carbon_limit, expected_color", [
    (None, 0x2ECC71),   # no limit set: green
    (1.0, 0x2ECC71),    # 0.005 gCO2 is below the limit: green
    (0.005, 0xE74C3C),  # equal to the limit counts as over it: red
    (0.001, 0xE74C3C),  # above the limit: red
])
@patch('requests.post')
def test_webhook_exporter_discord_color_follows_carbon_limit(mock_post, carbon_limit, expected_color):
    """The embed is green below carbon_limit (or without one) and red at or above it."""
    payload = _post_one_measurement(mock_post, carbon_emitted=0.005, carbon_limit=carbon_limit, format="discord")

    assert payload["embeds"][0]["color"] == expected_color


@patch('requests.post')
def test_webhook_exporter_slack_sends_block_kit_blocks(mock_post):
    """format="slack" sends Block Kit blocks and a plain text fallback with the function name, gCO2 and duration."""
    payload = _post_one_measurement(mock_post, format="slack")

    assert set(payload) == {"text", "blocks"}
    assert "test_function" in payload["text"]
    assert "0.005000 gCO2" in payload["text"]
    assert "1.20 s" in payload["text"]

    title, metrics = payload["blocks"]
    assert title == {"type": "section", "text": {"type": "plain_text", "text": "EcoTrace: test_function"}}
    assert metrics["type"] == "section"
    assert [field["text"] for field in metrics["fields"]] == ["*Carbon*\n0.005000 gCO2", "*Duration*\n1.20 s"]


@patch('requests.post')
def test_webhook_exporter_unknown_format_falls_back_to_json(mock_post, caplog):
    """An unknown format logs a warning and still sends the default JSON payload."""
    with caplog.at_level("WARNING", logger="ecotrace.exporters.webhook"):
        payload = _post_one_measurement(mock_post, format="teams")

    assert "Invalid format='teams'" in caplog.text
    assert set(payload) == {"function", "carbon_gco2", "duration_s", "region", "run_id", "run_label"}


from ecotrace.exporters.cloud import CloudExporter

@patch('requests.Session.post')
def test_cloud_exporter_registration_and_export(mock_post, tmp_path):
    """Verify CloudExporter formats payload and sends X-EcoTrace-Key header."""
    mock_post.return_value.status_code = 202

    exporter = CloudExporter(api_key="eco_usr_testkey123", retry_dir=str(tmp_path / "queue"))
    try:
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
    finally:
        exporter.close()

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
    eco._exporters[0].close()



