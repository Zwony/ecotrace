import json
import sys
import time
from unittest.mock import MagicMock, patch

import pytest

from ecotrace import EcoTrace
from ecotrace.gpu import (
    get_all_gpu_info,
    get_all_gpu_power_w,
    get_gpu_info,
    get_gpu_power_w,
)

# =========================================================================
# Angle 1 & 2 & 3: NVML Multi-GPU Enumeration (0, 1, 2, 4, 8 GPUs)
# =========================================================================

def test_get_all_gpu_info_zero_gpus():
    """Verify empty list is returned when NVML reports zero devices."""
    mock_nvml = MagicMock()
    mock_nvml.nvmlDeviceGetCount.return_value = 0

    with patch.dict(sys.modules, {"nvidia_ml_py": mock_nvml}), \
         patch("wmi.WMI", side_effect=ImportError):
        gpus = get_all_gpu_info({})
        assert gpus == []


def test_get_all_gpu_info_single_nvidia_gpu():
    """Verify single NVIDIA GPU detection returns correctly populated list."""
    mock_nvml = MagicMock()
    mock_nvml.nvmlDeviceGetCount.return_value = 1
    mock_handle = MagicMock()
    mock_nvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
    mock_nvml.nvmlDeviceGetName.return_value = "NVIDIA GeForce RTX 4090"
    mock_nvml.nvmlDeviceGetPowerManagementLimit.return_value = 450000  # 450W

    with patch.dict(sys.modules, {"nvidia_ml_py": mock_nvml}):
        gpus = get_all_gpu_info({})
        assert len(gpus) == 1
        assert gpus[0]["brand"] == "NVIDIA GeForce RTX 4090"
        assert gpus[0]["tdp"] == 450.0
        assert gpus[0]["type"] == "nvidia"
        assert gpus[0]["handle"] is mock_handle
        assert gpus[0]["index"] == 0


def test_get_all_gpu_info_multiple_nvidia_gpus():
    """Verify 4-GPU cluster enumeration with distinct handles and TDPs."""
    mock_nvml = MagicMock()
    mock_nvml.nvmlDeviceGetCount.return_value = 4

    handles = [MagicMock(name=f"handle_{i}") for i in range(4)]
    names = [f"NVIDIA A100-SXM4-80GB (GPU {i})" for i in range(4)]
    tdps = [400000, 400000, 400000, 400000]

    mock_nvml.nvmlDeviceGetHandleByIndex.side_effect = lambda idx: handles[idx]
    mock_nvml.nvmlDeviceGetName.side_effect = lambda h: names[handles.index(h)]
    mock_nvml.nvmlDeviceGetPowerManagementLimit.side_effect = lambda h: tdps[handles.index(h)]

    with patch.dict(sys.modules, {"nvidia_ml_py": mock_nvml}):
        gpus = get_all_gpu_info({})
        assert len(gpus) == 4
        for i, g in enumerate(gpus):
            assert g["index"] == i
            assert g["type"] == "nvidia"
            assert g["handle"] is handles[i]
            assert g["tdp"] == 400.0
            assert f"GPU {i}" in g["brand"]


# =========================================================================
# Angle 4: NVML String and Bytes Handling
# =========================================================================

def test_get_all_gpu_info_bytes_name_decoding():
    """Verify bytes returned by NVML are safely decoded and sanitized."""
    mock_nvml = MagicMock()
    mock_nvml.nvmlDeviceGetCount.return_value = 1
    mock_nvml.nvmlDeviceGetHandleByIndex.return_value = MagicMock()
    mock_nvml.nvmlDeviceGetName.return_value = b"Tesla V100-PCIE-32GB\xae"
    mock_nvml.nvmlDeviceGetPowerManagementLimit.return_value = 250000

    with patch.dict(sys.modules, {"nvidia_ml_py": mock_nvml}):
        gpus = get_all_gpu_info({})
        assert len(gpus) == 1
        assert "Tesla V100-PCIE-32GB" in gpus[0]["brand"]


# =========================================================================
# Angle 5: Non-NVIDIA WMI Fallbacks (Intel, AMD, Unknown)
# =========================================================================

def test_get_all_gpu_info_wmi_intel_and_amd():
    """Verify non-NVIDIA WMI devices are properly classified and mapped to defaults."""
    mock_wmi = MagicMock()
    gpu1 = MagicMock()
    gpu1.Name = "Intel(R) UHD Graphics 770"
    gpu2 = MagicMock()
    gpu2.Name = "AMD Radeon RX 6800 XT"
    mock_wmi.return_value.Win32_VideoController.return_value = [gpu1, gpu2]

    defaults = {"intel": 20.0, "amd": 300.0, "unknown": 100.0}

    with patch.dict(sys.modules, {"nvidia_ml_py": None}), \
         patch("wmi.WMI", mock_wmi):
        gpus = get_all_gpu_info(defaults)
        assert len(gpus) == 2
        assert gpus[0]["type"] == "intel"
        assert gpus[0]["tdp"] == 20.0
        assert gpus[0]["handle"] is None
        assert gpus[0]["index"] == 0

        assert gpus[1]["type"] == "amd"
        assert gpus[1]["tdp"] == 300.0
        assert gpus[1]["handle"] is None
        assert gpus[1]["index"] == 1


# =========================================================================
# Angle 6: Robustness to NVML Exceptions & Partial Hardware Failures
# =========================================================================

def test_get_all_gpu_info_nvml_init_fails_falls_back_to_wmi():
    """When nvmlInit raises an error, fallback seamlessly to WMI."""
    mock_nvml = MagicMock()
    mock_nvml.nvmlInit.side_effect = RuntimeError("NVML driver not loaded")

    mock_wmi = MagicMock()
    gpu = MagicMock()
    gpu.Name = "Intel Iris Xe Graphics"
    mock_wmi.return_value.Win32_VideoController.return_value = [gpu]

    with patch.dict(sys.modules, {"nvidia_ml_py": mock_nvml}), \
         patch("wmi.WMI", mock_wmi):
        gpus = get_all_gpu_info({"intel": 15.0})
        assert len(gpus) == 1
        assert gpus[0]["type"] == "intel"


def test_get_all_gpu_info_partial_device_failure():
    """When device 1 throws during enumeration, device 0 is still returned."""
    mock_nvml = MagicMock()
    mock_nvml.nvmlDeviceGetCount.return_value = 2

    handle0 = MagicMock()
    mock_nvml.nvmlDeviceGetHandleByIndex.side_effect = [handle0, RuntimeError("Device lost")]
    mock_nvml.nvmlDeviceGetName.return_value = "NVIDIA RTX 3080"
    mock_nvml.nvmlDeviceGetPowerManagementLimit.return_value = 320000

    with patch.dict(sys.modules, {"nvidia_ml_py": mock_nvml}):
        gpus = get_all_gpu_info({})
        assert len(gpus) == 1
        assert gpus[0]["index"] == 0


# =========================================================================
# Angle 7: get_all_gpu_power_w Multi-Device Power Aggregation
# =========================================================================

def test_get_all_gpu_power_w_empty_or_none():
    """Returns None for empty list or None."""
    assert get_all_gpu_power_w([]) is None
    assert get_all_gpu_power_w(None) is None


def test_get_all_gpu_power_w_missing_pynvml():
    """Returns None if nvidia_ml_py cannot be imported."""
    with patch.dict(sys.modules, {"nvidia_ml_py": None}):
        assert get_all_gpu_power_w([{"type": "nvidia", "handle": MagicMock()}]) is None


def test_get_all_gpu_power_w_single_device():
    """Reads power in watts (converting mW to W)."""
    mock_nvml = MagicMock()
    mock_handle = MagicMock()
    mock_nvml.nvmlDeviceGetPowerUsage.return_value = 150000  # 150W

    gpu_infos = [{"type": "nvidia", "handle": mock_handle, "index": 0}]

    with patch.dict(sys.modules, {"nvidia_ml_py": mock_nvml}):
        power = get_all_gpu_power_w(gpu_infos)
        assert power == pytest.approx(150.0)


def test_get_all_gpu_power_w_multi_device_sum():
    """Sums power draw across multiple NVIDIA GPUs."""
    mock_nvml = MagicMock()
    h0, h1, h2 = MagicMock(), MagicMock(), MagicMock()
    
    # GPU 0 draws 120W, GPU 1 draws 250W, GPU 2 draws 310W
    mock_nvml.nvmlDeviceGetPowerUsage.side_effect = lambda h: {
        h0: 120000,
        h1: 250000,
        h2: 310000,
    }[h]

    gpu_infos = [
        {"type": "nvidia", "handle": h0, "index": 0},
        {"type": "nvidia", "handle": h1, "index": 1},
        {"type": "nvidia", "handle": h2, "index": 2},
    ]

    with patch.dict(sys.modules, {"nvidia_ml_py": mock_nvml}):
        total_pwr = get_all_gpu_power_w(gpu_infos)
        assert total_pwr == pytest.approx(680.0)


def test_get_all_gpu_power_w_skips_non_nvidia_and_null_handles():
    """Ignores AMD, Intel, and devices with handle=None."""
    mock_nvml = MagicMock()
    h0 = MagicMock()
    mock_nvml.nvmlDeviceGetPowerUsage.return_value = 80000  # 80W

    gpu_infos = [
        {"type": "nvidia", "handle": h0, "index": 0},
        {"type": "amd", "handle": None, "index": 1},
        {"type": "intel", "handle": None, "index": 2},
        {"type": "nvidia", "handle": None, "index": 3},
    ]

    with patch.dict(sys.modules, {"nvidia_ml_py": mock_nvml}):
        total_pwr = get_all_gpu_power_w(gpu_infos)
        assert total_pwr == pytest.approx(80.0)
        assert mock_nvml.nvmlDeviceGetPowerUsage.call_count == 1


def test_get_all_gpu_power_w_partial_device_exception():
    """If one device throws when reading power, the others are still summed."""
    mock_nvml = MagicMock()
    h0, h1 = MagicMock(), MagicMock()

    mock_nvml.nvmlDeviceGetPowerUsage.side_effect = lambda h: 100000 if h == h0 else RuntimeError("Read error")

    gpu_infos = [
        {"type": "nvidia", "handle": h0, "index": 0},
        {"type": "nvidia", "handle": h1, "index": 1},
    ]

    with patch.dict(sys.modules, {"nvidia_ml_py": mock_nvml}):
        total_pwr = get_all_gpu_power_w(gpu_infos)
        assert total_pwr == pytest.approx(100.0)


def test_get_all_gpu_power_w_all_devices_fail():
    """If all devices throw when reading power, returns None."""
    mock_nvml = MagicMock()
    mock_nvml.nvmlDeviceGetPowerUsage.side_effect = RuntimeError("Driver failure")

    gpu_infos = [{"type": "nvidia", "handle": MagicMock(), "index": 0}]

    with patch.dict(sys.modules, {"nvidia_ml_py": mock_nvml}):
        assert get_all_gpu_power_w(gpu_infos) is None


# =========================================================================
# Angle 8: Backward Compatibility of get_gpu_info & get_gpu_power_w
# =========================================================================

def test_backward_compat_get_gpu_info_and_power():
    """Verify legacy single-GPU functions maintain exact previous behavior."""
    mock_nvml = MagicMock()
    mock_handle = MagicMock()
    mock_nvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
    mock_nvml.nvmlDeviceGetName.return_value = "NVIDIA RTX 4080"
    mock_nvml.nvmlDeviceGetPowerManagementLimit.return_value = 320000
    mock_nvml.nvmlDeviceGetPowerUsage.return_value = 160000

    with patch.dict(sys.modules, {"nvidia_ml_py": mock_nvml}):
        info = get_gpu_info(0, {})
        assert info["brand"] == "NVIDIA RTX 4080"
        assert info["tdp"] == 320.0
        assert info["type"] == "nvidia"

        power = get_gpu_power_w(info)
        assert power == pytest.approx(160.0)


# =========================================================================
# Angle 9: EcoTrace Multi-GPU Initialization & Option B Backward Compat
# =========================================================================

def test_ecotrace_multi_gpu_default_tracks_all():
    """EcoTrace(gpu_index=0) detects and stores all available GPUs."""
    mock_gpus = [
        {"brand": "GPU 0", "tdp": 250.0, "type": "nvidia", "handle": MagicMock(), "index": 0},
        {"brand": "GPU 1", "tdp": 250.0, "type": "nvidia", "handle": MagicMock(), "index": 1},
    ]

    with patch("ecotrace.core.get_all_gpu_info", return_value=mock_gpus):
        eco = EcoTrace(quiet=True)
        assert eco.gpu_count == 2
        assert len(eco.gpu_infos) == 2
        assert eco.gpu_info is mock_gpus[0]


def test_ecotrace_gpu_index_option_b_backward_compat():
    """EcoTrace(gpu_index=1) preserves legacy behavior and emits deprecation warning."""
    mock_gpus = [
        {"brand": "GPU 0", "tdp": 200.0, "type": "nvidia", "handle": MagicMock(), "index": 0},
        {"brand": "GPU 1", "tdp": 300.0, "type": "nvidia", "handle": MagicMock(), "index": 1},
    ]

    with patch("ecotrace.core.get_all_gpu_info", return_value=mock_gpus):
        with pytest.warns(DeprecationWarning, match="gpu_index is deprecated"):
            eco = EcoTrace(gpu_index=1, quiet=True)
        assert eco.gpu_count == 1
        assert len(eco.gpu_infos) == 1
        assert eco.gpu_info is not None
        assert eco.gpu_info["index"] == 1
        assert eco.gpu_info["brand"] == "GPU 1"


def test_ecotrace_zero_gpus_detected():
    """EcoTrace gracefully handles machines with zero GPUs."""
    with patch("ecotrace.core.get_all_gpu_info", return_value=[]):
        eco = EcoTrace(quiet=True)
        assert eco.gpu_count == 0
        assert eco.gpu_infos == []
        assert eco.gpu_info is None


# =========================================================================
# Angle 10: get_summary Surfaces gpu_count and Formatted GPU Names
# =========================================================================

def test_get_summary_surfaces_multi_gpu():
    """get_summary() includes gpu_count and combined GPU brand names."""
    mock_gpus = [
        {"brand": "NVIDIA A100", "tdp": 400.0, "type": "nvidia", "handle": MagicMock(), "index": 0},
        {"brand": "NVIDIA A100", "tdp": 400.0, "type": "nvidia", "handle": MagicMock(), "index": 1},
    ]

    with patch("ecotrace.core.get_all_gpu_info", return_value=mock_gpus):
        eco = EcoTrace(quiet=True)
        summary = eco.get_summary()
        hw = summary["hardware"]
        assert hw["gpu_count"] == 2
        assert hw["gpu"] == "NVIDIA A100, NVIDIA A100"


def test_get_summary_zero_gpus():
    """get_summary() returns gpu_count=0 and gpu=None when no GPU exists."""
    with patch("ecotrace.core.get_all_gpu_info", return_value=[]):
        eco = EcoTrace(quiet=True)
        summary = eco.get_summary()
        hw = summary["hardware"]
        assert hw["gpu_count"] == 0
        assert hw["gpu"] is None


# =========================================================================
# Angle 11: Background Sampling in Multi-GPU Environment
# =========================================================================

def test_gpu_monitor_worker_samples_multiple_gpus():
    """_gpu_monitor_worker samples all active handles and records average util & total power."""
    mock_nvml = MagicMock()
    h0, h1 = MagicMock(), MagicMock()

    util0 = MagicMock()
    util0.gpu = 60.0
    util1 = MagicMock()
    util1.gpu = 80.0
    mock_nvml.nvmlDeviceGetUtilizationRates.side_effect = lambda h: util0 if h == h0 else util1
    mock_nvml.nvmlDeviceGetPowerUsage.side_effect = lambda h: 100000 if h == h0 else 200000  # 100W + 200W = 300W

    mock_gpus = [
        {"brand": "GPU 0", "tdp": 200.0, "type": "nvidia", "handle": h0, "index": 0},
        {"brand": "GPU 1", "tdp": 250.0, "type": "nvidia", "handle": h1, "index": 1},
    ]

    with patch("ecotrace.core.get_all_gpu_info", return_value=mock_gpus), \
         patch.dict(sys.modules, {"nvidia_ml_py": mock_nvml}):
        eco = EcoTrace(quiet=True)
        eco._start_gpu_monitor()
        time.sleep(0.12)  # Allow ~2 samples
        eco._stop_gpu_monitor()

        assert len(eco._gpu_samples) > 0
        sample = eco._gpu_samples[-1]
        assert len(sample) == 3
        _ts, avg_util, total_pwr = sample
        assert avg_util == pytest.approx(70.0)  # (60 + 80) / 2
        assert total_pwr == pytest.approx(300.0)  # 100W + 200W


# =========================================================================
# Angle 12: track_gpu Decorator with Multi-GPU
# =========================================================================

def test_track_gpu_with_multi_gpu_exact_power():
    """track_gpu accumulates carbon from aggregate multi-GPU power."""
    mock_gpus = [
        {"brand": "GPU 0", "tdp": 200.0, "type": "nvidia", "handle": MagicMock(), "index": 0},
        {"brand": "GPU 1", "tdp": 200.0, "type": "nvidia", "handle": MagicMock(), "index": 1},
    ]

    with patch("ecotrace.core.get_all_gpu_info", return_value=mock_gpus):
        eco = EcoTrace(quiet=True)
        # Mock _get_avg_gpu_in_range to return (75% util, 400W aggregate power)
        with patch.object(eco, "_get_avg_gpu_in_range", return_value=(75.0, 400.0)):
            @eco.track_gpu
            def compute_step():
                time.sleep(0.01)
                return 42

            result = compute_step()
            assert result == 42
            assert eco.total_carbon > 0.0


def test_track_gpu_with_multi_gpu_estimation_mode():
    """When power reading is None, track_gpu sums TDP across all GPUs for estimation."""
    mock_gpus = [
        {"brand": "GPU 0", "tdp": 150.0, "type": "nvidia", "handle": None, "index": 0},
        {"brand": "GPU 1", "tdp": 250.0, "type": "nvidia", "handle": None, "index": 1},
    ]

    with patch("ecotrace.core.get_all_gpu_info", return_value=mock_gpus):
        eco = EcoTrace(quiet=True)
        # avg power is None -> estimation mode using total_tdp = 400W
        with patch.object(eco, "_get_avg_gpu_in_range", return_value=(80.0, None)):
            @eco.track_gpu
            def estimate_step():
                time.sleep(0.01)
                return "done"

            result = estimate_step()
            assert result == "done"
            assert eco.total_carbon > 0.0


def test_track_gpu_zero_gpus_graceful():
    """When no GPU is present, track_gpu executes cleanly without raising."""
    with patch("ecotrace.core.get_all_gpu_info", return_value=[]):
        eco = EcoTrace(quiet=True)

        @eco.track_gpu
        def no_gpu_task():
            return "ok"

        assert no_gpu_task() == "ok"


# =========================================================================
# Angle 13: track_block Context Manager Multi-GPU
# =========================================================================

def test_track_block_multi_gpu_aggregation():
    """track_block aggregates multi-GPU power during execution."""
    mock_gpus = [
        {"brand": "GPU 0", "tdp": 200.0, "type": "nvidia", "handle": MagicMock(), "index": 0},
        {"brand": "GPU 1", "tdp": 200.0, "type": "nvidia", "handle": MagicMock(), "index": 1},
    ]

    with patch("ecotrace.core.get_all_gpu_info", return_value=mock_gpus):
        eco = EcoTrace(quiet=True)
        with patch.object(eco, "_get_avg_gpu_in_range", return_value=(50.0, 300.0)):
            with eco.track_block("training_epoch"):
                time.sleep(0.01)

            assert eco.total_carbon > 0.0


# =========================================================================
# Angle 14: export_json Surfaces Multi-GPU Metadata
# =========================================================================

def test_export_json_includes_multi_gpu_metadata(tmp_path):
    """export_json includes total tdp_w, gpu_count, and brands."""
    mock_gpus = [
        {"brand": "RTX 4090", "tdp": 450.0, "type": "nvidia", "handle": MagicMock(), "index": 0},
        {"brand": "RTX 4090", "tdp": 450.0, "type": "nvidia", "handle": MagicMock(), "index": 1},
    ]

    json_file = str(tmp_path / "report.json")
    csv_file = str(tmp_path / "dummy.csv")

    with patch("ecotrace.core.get_all_gpu_info", return_value=mock_gpus):
        eco = EcoTrace(quiet=True)
        eco.export_json(filename=json_file, csv_path=csv_file)

        with open(json_file, "r") as f:
            data = json.load(f)

        gpu_meta = data["meta"]["gpu"]
        assert gpu_meta["gpu_count"] == 2
        assert gpu_meta["tdp_w"] == 900.0
        assert "RTX 4090, RTX 4090" in gpu_meta["brand"]
