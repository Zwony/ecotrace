"""Tracker-level tests for static carbon intensity after live grid failures."""

import json
import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from requests.exceptions import ConnectionError, Timeout

from ecotrace.core import EcoTrace


@pytest.fixture
def isolated_tracker_setup(monkeypatch):
    """Avoid unrelated configuration and hardware work during initialization."""
    monkeypatch.delenv("ECOTRACE_CLOUD_KEY", raising=False)
    with patch.multiple(
        "ecotrace.core",
        load_cli_config=Mock(return_value={}),
        load_tdp_database=Mock(return_value={}),
        get_cpu_info=Mock(return_value={"tdp": 65.0}),
        get_all_gpu_info=Mock(return_value=[]),
        get_ram_info=Mock(return_value={}),
        HardwareMonitor=Mock(),
    ), patch.object(EcoTrace, "_measure_idle_baseline", return_value=0.0):
        yield


@pytest.mark.parametrize(
    ("region", "network_error"),
    [
        ("DE", ConnectionError("Network unreachable")),
        ("FI", Timeout("Request timed out")),
    ],
)
def test_tracker_uses_regional_static_intensity_after_network_failure(
    region, network_error, isolated_tracker_setup, caplog
):
    constants_path = Path(__file__).resolve().parents[1] / "ecotrace" / "constants.json"
    constants = json.loads(constants_path.read_text(encoding="utf-8"))
    expected_intensity = constants["CARBON_INTENSITY_MAP"][region]

    with patch("requests.get", side_effect=network_error) as mock_get:
        tracker = EcoTrace(
            region_code=region,
            grid_api_key="test-grid-key",
            check_updates=False,
            quiet=True,
            session_summary=False,
        )

    mock_get.assert_called_once()
    assert tracker.region_code == region
    assert tracker.carbon_intensity == expected_intensity
    assert tracker._intensity_source == "static"
    assert any(
        record.name == "ecotrace"
        and record.levelno == logging.WARNING
        and "Live grid API unavailable, using static data." in record.getMessage()
        for record in caplog.records
    )
