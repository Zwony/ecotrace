"""EcoTrace ML framework callbacks.

Provides carbon and energy tracking integrations for popular ML frameworks:
- Hugging Face Transformers (`TrainerCallback`)
- PyTorch (manual training loops)
- Keras / TensorFlow (`model.fit`)

All framework dependencies are lazy-loaded on demand.
"""

from typing import Any

__all__ = [
    "EcoTraceCallback",
    "EcoTraceTrainerCallback",
    "EcoTraceHuggingFaceCallback",
    "EcoTracePyTorchCallback",
    "EcoTraceKerasCallback",
]


def __getattr__(name: str) -> Any:
    if name in ("EcoTraceCallback", "EcoTraceTrainerCallback", "EcoTraceHuggingFaceCallback"):
        from .huggingface import EcoTraceCallback, EcoTraceTrainerCallback, EcoTraceHuggingFaceCallback
        globals()["EcoTraceCallback"] = EcoTraceCallback
        globals()["EcoTraceTrainerCallback"] = EcoTraceTrainerCallback
        globals()["EcoTraceHuggingFaceCallback"] = EcoTraceHuggingFaceCallback
        return globals()[name]
    elif name == "EcoTracePyTorchCallback":
        from .pytorch import EcoTracePyTorchCallback
        globals()["EcoTracePyTorchCallback"] = EcoTracePyTorchCallback
        return EcoTracePyTorchCallback
    elif name == "EcoTraceKerasCallback":
        from .keras import EcoTraceKerasCallback
        globals()["EcoTraceKerasCallback"] = EcoTraceKerasCallback
        return EcoTraceKerasCallback
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
