import sys
import pytest
from unittest.mock import patch, MagicMock

# Define Keras mock stuff before importing callback
mock_keras_callback = MagicMock()
mock_tf = MagicMock()
mock_tf.keras.callbacks.Callback = mock_keras_callback

def setup_module():
    sys.modules["tensorflow"] = mock_tf
    sys.modules["tensorflow.keras"] = mock_tf.keras
    sys.modules["tensorflow.keras.callbacks"] = mock_tf.keras.callbacks

def teardown_module():
    sys.modules.pop("tensorflow", None)
    sys.modules.pop("tensorflow.keras", None)
    sys.modules.pop("tensorflow.keras.callbacks", None)

from ecotrace.callbacks.pytorch import EcoTracePyTorchCallback
from ecotrace.callbacks.keras import EcoTraceKerasCallback


def test_pytorch_callback_lifecycle(capsys):
    # Mock out EcoTraceML inside the callback
    mock_tracker = MagicMock()
    mock_tracker.gpu_info = {"brand": "Test NVIDIA GPU"}
    mock_tracker.snapshot_energy.return_value = (5000.0, [])
    mock_tracker.log_epoch.return_value = 0.0001
    mock_tracker.eco = MagicMock()
    mock_tracker.eco.carbon_intensity = 0.5

    with patch("ecotrace.callbacks.pytorch.EcoTraceML", return_value=mock_tracker):
        cb = EcoTracePyTorchCallback(
            model_name="ResNetTest",
            epochs=5,
            verbose=True
        )
        
        # Test training begin
        cb.on_train_begin()
        mock_tracker.__enter__.assert_called_once()
        captured = capsys.readouterr()
        assert "[EcoTrace] Training started — ResNetTest on Test NVIDIA GPU" in captured.out

        # Test epoch lifecycle
        # First epoch begin
        cb.on_epoch_begin(0)
        mock_tracker.snapshot_energy.assert_called()
        
        # Mock next snapshot returning higher energy (e.g. 5360 Joules, delta = 360 Joules = 0.0001 kWh)
        mock_tracker.snapshot_energy.return_value = (5360.0, [])
        cb.on_epoch_end(0, metrics={"loss": 0.35})
        
        from unittest.mock import ANY
        mock_tracker.log_epoch.assert_called_with(0, 360.0, ANY, {"loss": 0.35})
        captured = capsys.readouterr()
        assert "[EcoTrace] Epoch   0 — " in captured.out
        assert "loss=0.3500" in captured.out

        # Test training end
        cb.on_train_end()
        mock_tracker.__exit__.assert_called_once()
        captured = capsys.readouterr()
        assert "[EcoTrace] Training complete — 1 epochs" in captured.out
        assert "Total carbon" in captured.out


def test_keras_callback_lifecycle(capsys):
    mock_tracker = MagicMock()
    mock_tracker.gpu_info = {"brand": "Test AMD GPU"}
    mock_tracker.snapshot_energy.return_value = (1000.0, [])
    mock_tracker.log_epoch.return_value = 0.0001
    mock_tracker.eco = MagicMock()
    mock_tracker.eco.carbon_intensity = 0.4

    with patch("ecotrace.callbacks.keras.EcoTraceML", return_value=mock_tracker):
        cb = EcoTraceKerasCallback(
            model_name="KerasTest",
            epochs=10,
            verbose=True
        )
        
        # Verify set_model and set_params work
        cb.set_model("mock_model")
        cb.set_params({"epochs": 10})
        assert cb.model == "mock_model"
        assert cb.params == {"epochs": 10}

        # Test training begin
        cb.on_train_begin()
        mock_tracker.__enter__.assert_called_once()
        captured = capsys.readouterr()
        assert "[EcoTrace] Keras training started — KerasTest on Test AMD GPU" in captured.out

        # Test epoch lifecycle
        cb.on_epoch_begin(0)
        mock_tracker.snapshot_energy.return_value = (1360.0, [])
        cb.on_epoch_end(0, logs={"loss": 0.12})
        
        from unittest.mock import ANY
        mock_tracker.log_epoch.assert_called_with(0, 360.0, ANY, {"loss": 0.12})
        captured = capsys.readouterr()
        assert "[EcoTrace] Epoch   0 — " in captured.out
        assert "loss=0.1200" in captured.out

        # Test training end
        cb.on_train_end()
        mock_tracker.__exit__.assert_called_once()
        captured = capsys.readouterr()
        assert "[EcoTrace] Training complete — 1 epochs" in captured.out


def test_keras_callback_missing_tensorflow():
    # Temporarily remove tensorflow mock from sys.modules
    sys.modules.pop("tensorflow", None)
    sys.modules.pop("tensorflow.keras", None)
    sys.modules.pop("tensorflow.keras.callbacks", None)
    
    with pytest.raises(ImportError) as excinfo:
        EcoTraceKerasCallback(model_name="NoTFTest")
        
    assert "EcoTraceKerasCallback requires TensorFlow" in str(excinfo.value)
    
    # Restore mocks for other potential runs
    sys.modules["tensorflow"] = mock_tf
    sys.modules["tensorflow.keras"] = mock_tf.keras
    sys.modules["tensorflow.keras.callbacks"] = mock_tf.keras.callbacks
