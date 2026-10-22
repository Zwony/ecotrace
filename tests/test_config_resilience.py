"""Configuration failures must not prevent isolated tracker initialization."""

import json
import logging
from unittest.mock import Mock

import pytest

from ecotrace import config, core


@pytest.fixture(params=[config.load_constants, config.load_cli_config])
def loader(request):
    return request.param


@pytest.mark.parametrize(
    "contents",
    [b"", b"{\"region\":", b"region: [unfinished", b"\xff"],
    ids=["empty", "truncated-json", "malformed-yaml", "invalid-utf8"],
)
def test_unreadable_config_content_falls_back_to_empty_dict(
    tmp_path, loader, contents
):
    # Loaders accept JSON only: YAML text is invalid JSON, not YAML support.
    path = tmp_path / "config.json"
    path.write_bytes(contents)
    assert loader(path) == {}


def test_missing_config_falls_back_without_creating_a_file(tmp_path, loader):
    path = tmp_path / "missing.json"
    assert loader(path) == {}
    assert not path.exists()


def test_permission_error_reading_config_is_contained(
    tmp_path, monkeypatch, loader
):
    path = tmp_path / "config.json"
    path.write_text("{}", encoding="utf-8")
    denied = Mock(side_effect=PermissionError("synthetic read denial"))
    # Patch this module's open, not global builtins or real file permissions.
    monkeypatch.setattr(config, "open", denied, raising=False)

    assert loader(path) == {}
    denied.assert_called_once_with(path, "r", encoding="utf-8")


def test_valid_json_configuration_is_preserved(tmp_path, loader):
    path = tmp_path / "config.json"
    expected = {"CARBON_INTENSITY_MAP": {"TR": 321}, "label": "synthetic"}
    path.write_text(json.dumps(expected), encoding="utf-8")
    assert loader(path) == expected


@pytest.fixture
def make_tracker(monkeypatch):
    """Keep real validation but remove hardware, credentials and network IO."""
    keys = ("GEMINI_API_KEY", "ECOTRACE_GRID_API_KEY", "ECOTRACE_CLOUD_KEY")
    for key in keys:
        monkeypatch.delenv(key, raising=False)

    def reject_network(*args, **kwargs):
        pytest.fail("Configuration resilience tests must not use the network")

    monkeypatch.setattr("requests.sessions.Session.request", reject_network)
    for name, value in {
        "load_cli_config": {},
        "load_constants": {"CARBON_INTENSITY_MAP": {"TR": 321}},
        "load_tdp_database": {},
        "get_cpu_info": {"tdp": 65.0},
        "get_all_gpu_info": [],
        "get_ram_info": {},
        "identify_user_region": None,
    }.items():
        monkeypatch.setattr(core, name, Mock(return_value=value))
    monkeypatch.setattr(core, "HardwareMonitor", Mock())
    monkeypatch.setattr(core.psutil, "Process", Mock())
    monkeypatch.setattr(
        core.EcoTrace, "_measure_idle_baseline", lambda self: 0.0
    )
    trackers = []

    def create(**kwargs):
        options = dict(region_code="TR", check_updates=False,
                       quiet=True, session_summary=False)
        options.update(kwargs)
        tracker = core.EcoTrace(**options)
        trackers.append(tracker)
        return tracker

    yield create
    for tracker in trackers:
        tracker._exporter_pool.shutdown(wait=True)


@pytest.mark.parametrize("failure", ["invalid-json", "permission-error"])
def test_tracker_uses_defaults_after_constants_read_failure(
    tmp_path, monkeypatch, make_tracker, caplog, failure
):
    path = tmp_path / "constants.json"
    path.write_text("{", encoding="utf-8")
    if failure == "permission-error":
        monkeypatch.setattr(
            config, "open", Mock(side_effect=PermissionError("synthetic")),
            raising=False,
        )
    monkeypatch.setattr(
        core, "load_constants", lambda _: config.load_constants(path)
    )

    with caplog.at_level(logging.WARNING, logger="ecotrace"):
        tracker = make_tracker()

    assert tracker.region_code == config.DEFAULT_REGION
    assert tracker.carbon_intensity == config.DEFAULT_CARBON_INTENSITY
    assert tracker.gpu_tdp_defaults == {
        "intel": config.DEFAULT_GPU_TDP_INTEL_W,
        "amd": config.DEFAULT_GPU_TDP_AMD_W,
        "unknown": config.DEFAULT_GPU_TDP_UNKNOWN_W,
    }
    assert tracker._intensity_source == "static"
    assert tracker.cloud_key is None
    # Loading is silent; validation emits the real fallback warning.
    assert any(
        record.name == "ecotrace" and record.levelno == logging.WARNING
        and "Unmapped region code 'TR'. Defaulting to GLOBAL."
        in record.getMessage()
        for record in caplog.records
    )


@pytest.mark.parametrize(
    "argument,value,attribute,expected,warning",
    [
        ("gpu_index", -1, "gpu_index", 0, "Invalid gpu_index="),
        ("gpu_index", "bad", "gpu_index", 0, "Invalid gpu_index="),
        ("gpu_index", None, "gpu_index", 0, "Invalid gpu_index="),
        ("carbon_limit", 0, "carbon_limit", None, "Invalid carbon_limit="),
        ("carbon_limit", -1, "carbon_limit", None, "Invalid carbon_limit="),
        ("carbon_limit", "bad", "carbon_limit", None, "Invalid carbon_limit="),
        ("region_code", None, "region_code", "GLOBAL", "Invalid region code"),
        ("region_code", " ", "region_code", "GLOBAL", "Invalid region code"),
        ("region_code", "ZZ", "region_code", "GLOBAL", "Unmapped region code"),
    ],
)
def test_invalid_tracker_options_fall_back_with_a_warning(
    make_tracker, caplog, argument, value, attribute, expected, warning
):
    with caplog.at_level(logging.WARNING, logger="ecotrace"):
        tracker = make_tracker(**{argument: value})

    assert getattr(tracker, attribute) == expected
    assert any(
        record.name == "ecotrace" and record.levelno == logging.WARNING
        and warning in record.getMessage()
        for record in caplog.records
    )


def test_valid_tracker_options_are_not_replaced(make_tracker, caplog):
    tracker = make_tracker(region_code=" tr ", carbon_limit=2.5, gpu_index=0)
    assert tracker.region_code == "TR"
    assert tracker.carbon_intensity == 321
    assert tracker.carbon_limit == 2.5
    assert tracker.gpu_index == 0
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]
