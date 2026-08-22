"""EcoTrace v1.5.1 Validation Test Suite.

Independent, self-contained unit tests covering bug fixes, edge cases,
exporter dispatch, thread safety, region validation, and budget enforcement.
"""

import sys
import logging
import pytest
from unittest.mock import patch, MagicMock, call
from ecotrace import EcoTrace, __version__
from ecotrace.logger import logger
from ecotrace.config import validate_region_code, resolve_carbon_intensity, load_cli_config
from ecotrace.exporters.cloud import CloudExporter
from ecotrace.exporters.otel import OTelExporter
from ecotrace.exporters.webhook import WebhookExporter
from ecotrace.ml import EcoTraceML


def test_package_version_is_1_5_1():
    """Verify top-level package version is bumped to 1.5.1."""
    assert __version__ == "1.5.1"


def test_logger_default_level_is_warning():
    """Verify package logger level defaults to WARNING as documented."""
    assert logger.level == logging.WARNING


def test_exporters_module_lazy_loading():
    """Verify ecotrace.exporters module supports lazy attribute loading via __getattr__."""
    import ecotrace.exporters as exp_mod
    
    assert exp_mod.CloudExporter is CloudExporter
    assert exp_mod.OTelExporter is OTelExporter
    assert exp_mod.WebhookExporter is WebhookExporter
    
    with pytest.raises(AttributeError) as exc_info:
        _ = exp_mod.NonExistentExporter
    assert "has no attribute 'NonExistentExporter'" in str(exc_info.value)


def test_cloud_exporter_user_agent_contains_package_version():
    """Verify CloudExporter uses current package version in User-Agent header."""
    exporter = CloudExporter(api_key="eco_usr_test123")
    user_agent = exporter.session.headers.get("User-Agent", "")
    assert user_agent == f"EcoTrace-Python-Client/{__version__}"


def test_cloud_exporter_export_payload_structure():
    """Verify CloudExporter formats payload correctly including run_id and run_label."""
    exporter = CloudExporter(api_key="eco_usr_test123")
    
    with patch.object(exporter.session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp
        
        exporter.export(
            carbon_emitted=0.012345,
            func_name="process_dataset",
            duration=2.5,
            region="DE",
            run_id="run_abc123",
            run_label="experiment_1"
        )
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        payload = kwargs.get("json", {})
        
        assert payload["function"] == "process_dataset"
        assert payload["carbon_gco2"] == 0.012345
        assert payload["duration_s"] == 2.5
        assert payload["region"] == "DE"
        assert payload["run_id"] == "run_abc123"
        assert payload["run_label"] == "experiment_1"
        assert "recorded_at" in payload


def test_multiple_exporters_receive_dispatched_metrics():
    """Verify core engine dispatches metrics to multiple registered exporters simultaneously."""
    eco = EcoTrace(region_code="US", quiet=True, check_updates=False)
    
    exporter1 = MagicMock()
    exporter2 = MagicMock()
    eco.add_exporter(exporter1)
    eco.add_exporter(exporter2)
    
    def sample_func():
        return "done"
    
    eco.measure(sample_func)
    
    # Wait briefly for thread pool dispatch
    eco._exporter_pool.shutdown(wait=True)
    
    exporter1.export.assert_called_once()
    exporter2.export.assert_called_once()
    
    _, kwargs1 = exporter1.export.call_args
    assert kwargs1["func_name"] == "sample_func"
    assert kwargs1["run_id"] == eco._run_id
    assert kwargs1["run_label"] == eco._run_label


def test_exporter_signatures_accept_kwargs():
    """Verify all exporter implementations accept extra keyword arguments safely."""
    cloud_exp = CloudExporter(api_key="eco_usr_key")
    otel_exp = OTelExporter(ecotrace_instance=MagicMock())
    webhook_exp = WebhookExporter(ecotrace_instance=MagicMock(), url="https://example.com/webhook")
    
    # Should not raise TypeError when unexpected kwargs are passed
    with patch.object(cloud_exp.session, "post"):
        cloud_exp.export(0.01, "func", 1.0, "US", run_id="r1", run_label="l1", extra_param="ignored")
        
    otel_exp.export(0.01, "func", 1.0, "US", run_id="r1", run_label="l1", extra_param="ignored")
    
    if webhook_exp.url:
        with patch("requests.post"):
            webhook_exp.export(0.01, "func", 1.0, "US", run_id="r1", run_label="l1", extra_param="ignored")


def test_carbon_equivalence_formatting():
    """Verify equivalence method converts gCO2 magnitudes into human-readable comparisons."""
    eco = EcoTrace(quiet=True, check_updates=False)
    
    assert eco.equivalence(0.0) == ""
    assert eco.equivalence(-1.0) == ""
    assert "Google searches" in eco.equivalence(0.005)
    assert "LED bulb" in eco.equivalence(0.5)
    assert "smartphone charges" in eco.equivalence(5.0)
    assert "Netflix streaming" in eco.equivalence(50.0)
    assert "car driving" in eco.equivalence(500.0)


def test_compare_utility():
    """Verify EcoTrace.compare executes two functions and returns benchmark dictionary."""
    eco = EcoTrace(quiet=True, check_updates=False)
    
    def fn_a():
        return 10
    
    def fn_b():
        return 20
    
    res = eco.compare(fn_a, fn_b)
    assert "func1" in res
    assert "func2" in res
    assert res["func1"]["result"] == 10
    assert res["func2"]["result"] == 20
    assert res["func1"]["func_name"] == "fn_a"
    assert res["func2"]["func_name"] == "fn_b"


def test_validate_region_code_handling():
    """Verify region code validation handles uppercase, lowercase, whitespace, and unknown codes."""
    constants = {"CARBON_INTENSITY_MAP": {"US": 400, "DE": 350, "TR": 450}}
    
    assert validate_region_code("us", constants) == "US"
    assert validate_region_code(" de ", constants) == "DE"
    assert validate_region_code(None, constants) == "GLOBAL"
    assert validate_region_code(123, constants) == "GLOBAL"
    assert validate_region_code("INVALID_ZONE", constants) == "GLOBAL"


def test_carbon_budget_enforcement_and_callbacks():
    """Verify two-tier carbon budget warnings and custom callback execution."""
    callback_mock = MagicMock()
    eco = EcoTrace(carbon_limit=0.010, on_budget_exceeded=callback_mock, quiet=True, check_updates=False)
    
    # 1. Below 80% threshold (0.005 gCO2)
    eco._accumulate_carbon(0.005, "fn1", 1.0)
    assert not eco._budget_warning_fired
    assert not eco._budget_exceeded_fired
    callback_mock.assert_not_called()
    
    # 2. Reaching 80% threshold (0.008 gCO2 total)
    eco._accumulate_carbon(0.003, "fn2", 1.0)
    assert eco._budget_warning_fired
    assert not eco._budget_exceeded_fired
    callback_mock.assert_not_called()
    
    # 3. Exceeding 100% threshold (0.012 gCO2 total)
    eco._accumulate_carbon(0.004, "fn3", 1.0)
    assert eco._budget_exceeded_fired
    callback_mock.assert_called_once_with(eco.total_carbon, 0.010)


def test_nested_track_block_execution():
    """Verify nested track_block context managers calculate metrics without interference."""
    eco = EcoTrace(quiet=True, check_updates=False)
    
    with eco.track_block("outer_block"):
        sum_val = 0
        for i in range(100):
            sum_val += i
        with eco.track_block("inner_block"):
            sum_val *= 2
            
    assert eco._tracked_functions_count == 2
    assert eco.total_carbon > 0.0


def test_ecotrace_ml_snapshot_and_epoch_logging(tmp_path):
    """Verify EcoTraceML energy snapshotting and epoch audit logging."""
    ml_tracker = EcoTraceML(model_name="TestClassifier")
    
    # Simulate energy accumulation
    ml_tracker.total_gpu_energy_joules = 7200.0
    ml_tracker.power_history = [(100.0, 50.0), (101.0, 50.0)]
    
    joules, history = ml_tracker.snapshot_energy()
    assert joules == 7200.0
    assert len(history) == 2
    
    log_csv = tmp_path / "test_ml_log.csv"
    with patch("ecotrace.ml.os.path.exists", return_value=False), \
         patch("ecotrace.ml.open", create=True) as mock_open:
        co2 = ml_tracker.log_epoch(epoch=1, energy_j=3600.0, duration_s=10.0, metrics={"loss": 0.25})
        assert co2 > 0.0
        mock_open.assert_called_once()
