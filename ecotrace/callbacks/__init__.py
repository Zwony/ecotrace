"""EcoTrace ML framework callbacks.

Provides carbon and energy tracking integrations for popular ML frameworks:
- Hugging Face Transformers (`TrainerCallback`)
- PyTorch (manual training loops)
- Keras / TensorFlow (`model.fit`)
- LangChain (LLM, chat model, chain and agent calls)

All framework dependencies are lazy-loaded on demand.
"""

from typing import Any

__all__ = [
    "EcoTraceCallback",
    "EcoTraceTrainerCallback",
    "EcoTraceHuggingFaceCallback",
    "EcoTracePyTorchCallback",
    "EcoTraceKerasCallback",
    "EcoTraceLangChainCallback",
    "EcoTraceLangChainHandler",
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
    elif name in ("EcoTraceLangChainCallback", "EcoTraceLangChainHandler"):
        from .langchain import EcoTraceLangChainCallback, EcoTraceLangChainHandler
        globals()["EcoTraceLangChainCallback"] = EcoTraceLangChainCallback
        globals()["EcoTraceLangChainHandler"] = EcoTraceLangChainHandler
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
